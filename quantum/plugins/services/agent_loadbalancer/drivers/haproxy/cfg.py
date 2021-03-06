# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 New Dream Network, LLC (DreamHost)
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Mark McClain, DreamHost

import itertools

from quantum.agent.linux import utils
from quantum.plugins.common import constants as qconstants
from quantum.plugins.services.agent_loadbalancer import constants


PROTOCOL_MAP = {
    constants.PROTOCOL_TCP: 'tcp',
    constants.PROTOCOL_HTTP: 'http',
    constants.PROTOCOL_HTTPS: 'tcp',
}

BALANCE_MAP = {
    constants.LB_METHOD_ROUND_ROBIN: 'roundrobin',
    constants.LB_METHOD_LEAST_CONNECTIONS: 'leastconn',
    constants.LB_METHOD_SOURCE_IP: 'source'
}

ACTIVE = qconstants.ACTIVE


def save_config(conf_path, logical_config, socket_path=None):
    """Convert a logical configuration to the HAProxy version"""
    data = []
    data.extend(_build_global(logical_config, socket_path=socket_path))
    data.extend(_build_defaults(logical_config))
    data.extend(_build_frontend(logical_config))
    data.extend(_build_backend(logical_config))
    utils.replace_file(conf_path, '\n'.join(data))


def _build_global(config, socket_path=None):
    opts = [
        'daemon',
        'user nobody',
        'group nogroup',
        'log /dev/log local0',
        'log /dev/log local1 notice'
    ]

    if socket_path:
        opts.append('stats socket %s mode 0666 level user' % socket_path)

    return itertools.chain(['global'], ('\t' + o for o in opts))


def _build_defaults(config):
    opts = [
        'log global',
        'retries 3',
        'option redispatch',
        'timeout connect 5000',
        'timeout client 50000',
        'timeout server 50000',
    ]

    return itertools.chain(['defaults'], ('\t' + o for o in opts))


def _build_frontend(config):
    protocol = config['vip']['protocol']

    opts = [
        'option tcplog',
        'bind %s:%d' % (
            _get_first_ip_from_port(config['vip']['port']),
            config['vip']['protocol_port']
        ),
        'mode %s' % PROTOCOL_MAP[protocol],
        'default_backend %s' % config['pool']['id'],
    ]

    if config['vip']['connection_limit'] >= 0:
        opts.append('maxconn %s' % config['vip']['connection_limit'])

    if protocol == constants.PROTOCOL_HTTP:
        opts.append('option forwardfor')

    return itertools.chain(
        ['frontend %s' % config['vip']['id']],
        ('\t' + o for o in opts)
    )


def _build_backend(config):
    protocol = config['pool']['protocol']
    lb_method = config['pool']['lb_method']

    opts = [
        'mode %s' % PROTOCOL_MAP[protocol],
        'balance %s' % BALANCE_MAP.get(lb_method, 'roundrobin')
    ]

    if protocol == constants.PROTOCOL_HTTP:
        opts.append('option forwardfor')

    # add the first health_monitor (if available)
    server_addon, health_opts = _get_server_health_option(config)
    opts.extend(health_opts)

    # add the members
    opts.extend(
        (('server %(id)s %(address)s:%(protocol_port)s '
         'weight %(weight)s') % member) + server_addon
        for member in config['members']
        if (member['status'] == ACTIVE and member['admin_state_up'])
    )

    return itertools.chain(
        ['backend %s' % config['pool']['id']],
        ('\t' + o for o in opts)
    )


def _get_first_ip_from_port(port):
    for fixed_ip in port['fixed_ips']:
        return fixed_ip['ip_address']


def _get_server_health_option(config):
    """return the first active health option"""
    for monitor in config['healthmonitors']:
        if monitor['status'] == ACTIVE and monitor['admin_state_up']:
            break
    else:
        return '', []

    server_addon = ' check inter %(delay)ds fall %(max_retries)d' % monitor
    opts = [
        'timeout check %ds' % monitor['timeout']
    ]

    if monitor['type'] in (constants.HEALTH_MONITOR_HTTP,
                           constants.HEALTH_MONITOR_HTTPS):
        opts.append('option httpchk %(http_method)s %(url_path)s' % monitor)
        opts.append(
            'http-check expect rstatus %s' %
            '|'.join(_expand_expected_codes(monitor['expected_codes']))
        )

    if monitor['type'] == constants.HEALTH_MONITOR_HTTPS:
        opts.append('option ssl-hello-chk')

    return server_addon, opts


def _expand_expected_codes(codes):
    """Expand the expected code string in set of codes.

    200-204 -> 200, 201, 202, 204
    200, 203 -> 200, 203
    """

    retval = set()
    for code in codes.replace(',', ' ').split(' '):
        code = code.strip()

        if not code:
            continue
        elif '-' in code:
            low, hi = code.split('-')[:2]
            retval.update(str(i) for i in xrange(int(low), int(hi)))
        else:
            retval.add(code)
    return retval
