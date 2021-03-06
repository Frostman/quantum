# Copyright (c) 2012 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import mock

from quantum.extensions import portbindings
from quantum.openstack.common import importutils
from quantum.plugins.brocade import QuantumPlugin as brocade_plugin
from quantum.tests.unit import _test_extension_portbindings as test_bindings
from quantum.tests.unit import test_db_plugin as test_plugin


PLUGIN_NAME = ('quantum.plugins.brocade.'
               'QuantumPlugin.BrocadePluginV2')
NOS_DRIVER = ('quantum.plugins.brocade.'
              'nos.fake_nosdriver.NOSdriver')
FAKE_IPADDRESS = '2.2.2.2'
FAKE_USERNAME = 'user'
FAKE_PASSWORD = 'password'
FAKE_PHYSICAL_INTERFACE = 'em1'


class BrocadePluginV2TestCase(test_plugin.QuantumDbPluginV2TestCase):
    _plugin_name = PLUGIN_NAME

    def setUp(self):

        def mocked_brocade_init(self):

            self._switch = {'address': FAKE_IPADDRESS,
                            'username': FAKE_USERNAME,
                            'password': FAKE_PASSWORD
                            }
            self._driver = importutils.import_object(NOS_DRIVER)

        with mock.patch.object(brocade_plugin.BrocadePluginV2,
                               'brocade_init', new=mocked_brocade_init):
            super(BrocadePluginV2TestCase, self).setUp(self._plugin_name)


class TestBrocadeBasicGet(test_plugin.TestBasicGet,
                          BrocadePluginV2TestCase):
    pass


class TestBrocadeV2HTTPResponse(test_plugin.TestV2HTTPResponse,
                                BrocadePluginV2TestCase):
    pass


class TestBrocadePortsV2(test_plugin.TestPortsV2,
                         BrocadePluginV2TestCase,
                         test_bindings.PortBindingsTestCase):

    VIF_TYPE = portbindings.VIF_TYPE_BRIDGE
    HAS_PORT_FILTER = True


class TestBrocadeNetworksV2(test_plugin.TestNetworksV2,
                            BrocadePluginV2TestCase):
    pass
