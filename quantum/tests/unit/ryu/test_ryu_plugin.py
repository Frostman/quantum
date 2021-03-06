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

from quantum.tests.unit.ryu import fake_ryu
from quantum.tests.unit import test_db_plugin as test_plugin


class RyuPluginV2TestCase(test_plugin.QuantumDbPluginV2TestCase):

    _plugin_name = 'quantum.plugins.ryu.ryu_quantum_plugin.RyuQuantumPluginV2'

    def setUp(self):
        self.ryu_patcher = fake_ryu.patch_fake_ryu_client()
        self.ryu_patcher.start()
        super(RyuPluginV2TestCase, self).setUp(self._plugin_name)
        self.addCleanup(self.ryu_patcher.stop)


class TestRyuBasicGet(test_plugin.TestBasicGet, RyuPluginV2TestCase):
    pass


class TestRyuV2HTTPResponse(test_plugin.TestV2HTTPResponse,
                            RyuPluginV2TestCase):
    pass


class TestRyuPortsV2(test_plugin.TestPortsV2, RyuPluginV2TestCase):
    pass


class TestRyuNetworksV2(test_plugin.TestNetworksV2, RyuPluginV2TestCase):
    pass
