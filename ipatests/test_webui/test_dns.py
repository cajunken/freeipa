# Authors:
#   Petr Vobornik <pvoborni@redhat.com>
#
# Copyright (C) 2013  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
DNS tests
"""

from ipatests.test_webui.ui_driver import UI_driver

ZONE_ENTITY = 'dnszone'
RECORD_ENTITY = 'dnsrecord'
CONFIG_ENTITY = 'dnsconfig'

ZONE_DEFAULT_FACET = 'records'

ZONE_PKEY = 'foo.itest'

ZONE_DATA = {
    'pkey': ZONE_PKEY,
    'add': [
        ('textbox', 'idnsname', ZONE_PKEY),
        ('textbox', 'idnssoamname', 'ns'),
        ('textbox', 'ip_address', '192.168.1.1'),
        ('checkbox', 'force', ''),
    ],
    'mod': [
        ('checkbox', 'idnsallowsyncptr', ''),
    ],
}


RECORD_PKEY = 'itest'
A_IP = '192.168.1.10'
RECORD_ADD_DATA = {
    'pkey': RECORD_PKEY,
    'add': [
        ('textbox', 'idnsname', RECORD_PKEY),
        ('textbox', 'a_part_ip_address', A_IP),
    ]
}

RECORD_MOD_DATA = {
    'fields': [
        ('textbox', 'a_part_ip_address', '192.168.1.11'),
    ]
}

CONFIG_MOD_DATA = {
    'mod': [
        ('checkbox', 'idnsallowsyncptr', ''),
    ],
}


class test_dns(UI_driver):

    def __init__(self, *args, **kwargs):
        super(test_dns, self).__init__(args, kwargs)

        if not self.has_dns():
            self.skip('DNS not configured')

    def test_zone_record_crud(self):
        """
        Basic CRUD: dns
        """
        self.init_app()

        # add and mod zone
        self.basic_crud(ZONE_ENTITY, ZONE_DATA,
                        default_facet=ZONE_DEFAULT_FACET, delete=False)

        # add and mod record
        self.navigate_to_record(ZONE_PKEY)
        self.add_record(ZONE_ENTITY, RECORD_ADD_DATA,
                        facet=ZONE_DEFAULT_FACET, navigate=False)
        self.navigate_to_record(RECORD_PKEY)
        self.add_table_record('arecord', RECORD_MOD_DATA)

        # del record, del zone
        self.navigate_by_breadcrumb(ZONE_PKEY)
        self.delete_record(RECORD_PKEY)
        self.navigate_by_breadcrumb("DNS Zones")
        self.delete_record(ZONE_PKEY)

    def test_last_entry_deletion(self):
        """
        Test last entry deletion
        """
        self.init_app()
        self.add_record(ZONE_ENTITY, ZONE_DATA)
        self.navigate_to_record(ZONE_PKEY)
        self.add_record(ZONE_ENTITY, RECORD_ADD_DATA,
                        facet=ZONE_DEFAULT_FACET)
        self.navigate_to_record(RECORD_PKEY)
        self.delete_record(A_IP, parent=self.get_facet(), table_name='arecord')
        self.assert_dialog('message_dialog')
        self.dialog_button_click('ok')
        self.wait_for_request(n=2)
        self.assert_facet(ZONE_ENTITY, ZONE_DEFAULT_FACET)
        self.navigate_by_breadcrumb("DNS Zones")
        self.delete_record(ZONE_PKEY)

    def test_config_crud(self):
        """
        Basic CRUD: dnsconfig
        """
        self.init_app()
        self.navigate_by_menu('identity/dns/dnsconfig')
        self.mod_record(CONFIG_ENTITY, CONFIG_MOD_DATA)
