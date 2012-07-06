#    Copyright 2011 OpenStack LLC
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

from reddwarfclient import exceptions

from proboscis import before_class
from proboscis import test
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_raises
from proboscis.asserts import assert_true
from proboscis.check import Check

import tests
from tests.util import test_config
from tests.util import create_client
from tests.util import create_dbaas_client
from tests.util.users import Requirements
from tests.util.check import TypeCheck

from tests.api.instances import CreateInstance
from tests.api.instances import instance_info
from tests.api.instances import GROUP_START
from tests.api.instances import GROUP_TEST


GROUP = "dbaas.api.mgmt.instances"

@test(groups=[GROUP])
def mgmt_index_requires_admin_account():
    """ Verify that an admin context is required to call this function. """
    client = create_client(is_admin=False)
    assert_raises(exceptions.Unauthorized, client.management.index)



@test(depends_on_groups=[GROUP_START], groups=[GROUP, GROUP_TEST])
def mgmt_instance_get():
    """ Tests the mgmt instances index method. """
    client = create_client(is_admin=True)
    mgmt = client.management
    # Grab the info.id created by the main instance test which is stored in
    # a global.
    id = instance_info.id
    instance = mgmt.show(id)
    # Print out all fields for extra info if the test fails.
    for name in dir(instance):
        print(str(name) + "=" + str(getattr(instance, name)))
    with TypeCheck("instance", instance) as instance:
        #TODO: Figure out why we no longer have the commented out fields.
        instance.has_field('deleted', bool)
        #instance.has_field('deleted_at', basestring) #???
        instance.has_field('host', basestring)
        #instance.has_field('hostname', basestring)
        instance.has_field('id', basestring)
        instance.has_field('name', basestring)
        instance.has_field('server_id', basestring)
        #instance.has_field('server_status', basestring)
        instance.has_field('status', basestring)
        instance.has_field('tenant_id', basestring)
        instance.has_field('updated', basestring)
        #TODO: Validate additional fields, assert no extra fields exist.


@test(depends_on_classes=[CreateInstance], groups=[GROUP], enabled=False)
class MgmtInstancesIndex(object):
    """ Tests the mgmt instances index method. """

    @before_class
    def setUp(self):
        reqs = Requirements(is_admin=True)
        self.user = test_config.users.find_user(reqs)
        self.client = create_dbaas_client(self.user)

    @test
    def test_mgmt_instance_index_fields_present(self):
        """
        Verify that all the expected fields are returned by the index method.
        """
        expected_fields = [
                'account_id',
                'id',
                'host',
                'status',
                'created_at',
                'deleted_at',
                'deleted',
                'flavorid',
                'ips',
                'volumes'
            ]
        index = self.client.management.index()
        for instance in index:
            for field in expected_fields:
                assert_true(hasattr(instance, field))

    @test
    def test_mgmt_instance_index_check_filter(self):
        """
        Make sure that the deleted= filter works as expected, and no instances
        are excluded.
        """
        instance_counts = []
        for deleted_filter in (True, False):
            filtered_index = self.client.management.index(
                deleted=deleted_filter)
            instance_counts.append(len(filtered_index))
            for instance in filtered_index:
                # Every instance listed here should have the proper value
                # for 'deleted'.
                assert_equal(deleted_filter, instance.deleted)
        full_index = self.client.management.index()
        # There should be no instances that are neither deleted or not-deleted.
        assert_equal(len(full_index), sum(instance_counts))
