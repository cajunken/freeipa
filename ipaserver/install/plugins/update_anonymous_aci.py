# Authors:
#   Rob Crittenden <rcritten@redhat.com>
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

from copy import deepcopy
from ipaserver.install.plugins import FIRST, LAST
from ipaserver.install.plugins.baseupdate import PostUpdate
from ipalib import api, errors
from ipalib.aci import ACI
from ipalib.plugins import aci
from ipapython.ipa_log_manager import *

class update_anonymous_aci(PostUpdate):
    """
    Update the Anonymous ACI to ensure that all secrets are protected.
    """
    order = FIRST

    def execute(self, **options):
        aciname = u'Enable Anonymous access'
        aciprefix = u'none'
        ldap = self.obj.backend
        targetfilter = '(&(!(objectClass=ipaToken))(!(objectClass=ipatokenTOTP))(!(objectClass=ipatokenRadiusConfiguration)))'
        filter = None

        (dn, entry_attrs) = ldap.get_entry(api.env.basedn, ['aci'])

        acistrs = entry_attrs.get('aci', [])
        acilist = aci._convert_strings_to_acis(entry_attrs.get('aci', []))
        try:
            rawaci = aci._find_aci_by_name(acilist, aciprefix, aciname)
        except errors.NotFound:
            root_logger.error('Anonymous ACI not found, cannot update it')
            return False, False, []

        attrs = rawaci.target['targetattr']['expression']
        rawfilter = rawaci.target.get('targetfilter', None)
        if rawfilter is not None:
            filter = rawfilter['expression']

        update_attrs = deepcopy(attrs)

        needed_attrs = []
        for attr in ('ipaNTTrustAuthOutgoing', 'ipaNTTrustAuthIncoming'):
            if attr not in attrs:
                needed_attrs.append(attr)

        update_attrs.extend(needed_attrs)
        if (len(attrs) == len(update_attrs) and
            filter == targetfilter):
            root_logger.debug("Anonymous ACI already update-to-date")
            return (False, False, [])

        for tmpaci in acistrs:
            candidate = ACI(tmpaci)
            if rawaci.isequal(candidate):
                acistrs.remove(tmpaci)
                break

        if len(attrs) != len(update_attrs):
            root_logger.debug("New Anonymous ACI attributes needed: %s",
                needed_attrs)

            rawaci.target['targetattr']['expression'] = update_attrs

        if filter != targetfilter:
            root_logger.debug("New Anonymous ACI targetfilter needed.")

            rawaci.set_target_filter(targetfilter)

        acistrs.append(unicode(rawaci))
        entry_attrs['aci'] = acistrs

        try:
            ldap.update_entry(dn, entry_attrs)
        except Exception, e:
            root_logger.error("Failed to update Anonymous ACI: %s" % e)

        return (False, False, [])

api.register(update_anonymous_aci)
