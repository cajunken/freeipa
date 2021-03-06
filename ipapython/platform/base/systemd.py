# Author: Alexander Bokovoy <abokovoy@redhat.com>
#
# Copyright (C) 2011   Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os

from ipapython import ipautil
from ipapython.platform import base
from ipalib import api

class SystemdService(base.PlatformService):
    SYSTEMD_ETC_PATH = "/etc/systemd/system/"
    SYSTEMD_LIB_PATH = "/lib/systemd/system/"
    SYSTEMD_SRV_TARGET = "%s.target.wants"

    def __init__(self, service_name, systemd_name):
        super(SystemdService, self).__init__(service_name)
        self.systemd_name = systemd_name
        self.lib_path = os.path.join(self.SYSTEMD_LIB_PATH, self.systemd_name)
        self.lib_path_exists = None

    def service_instance(self, instance_name, operation=None):
        if self.lib_path_exists is None:
            self.lib_path_exists = os.path.exists(self.lib_path)

        elements = self.systemd_name.split("@")

        # Make sure the correct DS instance is returned
        if (elements[0] == 'dirsrv' and
                not instance_name and
                operation == 'is-active'):
            return 'dirsrv@%s.service' % str(api.env.realm.replace('.', '-'))

        # Short-cut: if there is already exact service name, return it
        if self.lib_path_exists and len(instance_name) == 0:
            if len(elements) == 1:
                # service name is like pki-tomcatd.target or krb5kdc.service
                return self.systemd_name
            if len(elements) > 1 and elements[1][0] != '.':
                # Service name is like pki-tomcatd@pki-tomcat.service and that file exists
                return self.systemd_name

        if len(elements) > 1:
            # We have dynamic service
            if len(instance_name) > 0:
                # Instanciate dynamic service
                return "%s@%s.service" % (elements[0], instance_name)
            else:
                # No instance name, try with target
                tgt_name = "%s.target" % (elements[0])
                srv_lib = os.path.join(self.SYSTEMD_LIB_PATH, tgt_name)
                if os.path.exists(srv_lib):
                    return tgt_name

        return self.systemd_name

    def parse_variables(self, text, separator=None):
        """
        Parses 'systemctl show' output and returns a dict[variable]=value
        Arguments: text -- 'systemctl show' output as string
                   separator -- optional (defaults to None), what separates the key/value pairs in the text
        """
        def splitter(x, separator=None):
            if len(x) > 1:
                y = x.split(separator)
                return (y[0], y[-1])
            return (None,None)
        return dict(map(lambda x: splitter(x, separator=separator), text.split("\n")))

    def __wait_for_open_ports(self, instance_name=""):
        """
        If this is a service we need to wait for do so.
        """
        ports = None
        if instance_name in base.wellknownports:
            ports = base.wellknownports[instance_name]
        else:
            elements = self.systemd_name.split("@")
            if elements[0] in base.wellknownports:
                ports = base.wellknownports[elements[0]]
        if ports:
            ipautil.wait_for_open_ports('localhost', ports, api.env.startup_timeout)

    def stop(self, instance_name="", capture_output=True):
        instance = self.service_instance(instance_name)
        args = ["/bin/systemctl", "stop", instance]

        # The --ignore-dependencies switch is used to avoid possible
        # deadlock during the shutdown transaction. For more details, see
        # https://fedorahosted.org/freeipa/ticket/3729#comment:1 and
        # https://bugzilla.redhat.com/show_bug.cgi?id=973331#c11
        if instance == "ipa-otpd.socket":
            args.append("--ignore-dependencies")

        ipautil.run(args, capture_output=capture_output)

        if 'context' in api.env and api.env.context in ['ipactl', 'installer']:
            update_service_list = True
        else:
            update_service_list = False
        super(SystemdService, self).stop(instance_name,update_service_list=update_service_list)

    def start(self, instance_name="", capture_output=True, wait=True):
        ipautil.run(["/bin/systemctl", "start", self.service_instance(instance_name)], capture_output=capture_output)
        if 'context' in api.env and api.env.context in ['ipactl', 'installer']:
            update_service_list = True
        else:
            update_service_list = False
        if wait and self.is_running(instance_name):
            self.__wait_for_open_ports(self.service_instance(instance_name))
        super(SystemdService, self).start(instance_name, update_service_list=update_service_list)

    def restart(self, instance_name="", capture_output=True, wait=True):
        # Restart command is broken before systemd-36-3.fc16
        # If you have older systemd version, restart of dependent services will hang systemd indefinetly
        ipautil.run(["/bin/systemctl", "restart", self.service_instance(instance_name)], capture_output=capture_output)
        if wait and self.is_running(instance_name):
            self.__wait_for_open_ports(self.service_instance(instance_name))

    def is_running(self, instance_name=""):
        instance = self.service_instance(instance_name, 'is-active')

        while True:
            try:
                (sout, serr, rcode) = ipautil.run(
                    ["/bin/systemctl", "is-active", instance],
                    capture_output=True
                )
            except ipautil.CalledProcessError as e:
                if e.returncode == 3 and 'activating' in str(e.output):
                    continue
                return False
            else:
                # activating
                if rcode == 3 and 'activating' in str(sout):
                    continue
                # active
                if rcode == 0:
                    return True
                # not active
                return False

    def is_installed(self):
        installed = True
        try:
            (sout,serr,rcode) = ipautil.run(["/bin/systemctl", "list-unit-files", "--full"])
            if rcode != 0:
                installed = False
            else:
                svar = self.parse_variables(sout)
                if not self.service_instance("") in svar:
                    # systemd doesn't show the service
                    installed = False
        except ipautil.CalledProcessError, e:
                installed = False
        return installed

    def is_enabled(self, instance_name=""):
        enabled = True
        try:
            (sout,serr,rcode) = ipautil.run(["/bin/systemctl", "is-enabled", self.service_instance(instance_name)])
            if rcode != 0:
                enabled = False
        except ipautil.CalledProcessError, e:
                enabled = False
        return enabled

    def enable(self, instance_name=""):
        if self.lib_path_exists is None:
            self.lib_path_exists = os.path.exists(self.lib_path)
        elements = self.systemd_name.split("@")
        l = len(elements)

        if self.lib_path_exists and (l > 1 and elements[1][0] != '.'):
            # There is explicit service unit supporting this instance, follow normal systemd enabler
            self.__enable(instance_name)
            return

        if self.lib_path_exists and (l == 1):
            # There is explicit service unit which does not support the instances, ignore instance
            self.__enable()
            return

        if len(instance_name) > 0 and l > 1:
            # New instance, we need to do following:
            # 1. Make /etc/systemd/system/<service>.target.wants/ if it is not there
            # 2. Link /etc/systemd/system/<service>.target.wants/<service>@<instance_name>.service to
            #    /lib/systemd/system/<service>@.service
            srv_tgt = os.path.join(self.SYSTEMD_ETC_PATH, self.SYSTEMD_SRV_TARGET % (elements[0]))
            srv_lnk = os.path.join(srv_tgt, self.service_instance(instance_name))
            try:
                if not ipautil.dir_exists(srv_tgt):
                    os.mkdir(srv_tgt)
                if os.path.exists(srv_lnk):
                    # Remove old link
                    os.unlink(srv_lnk)
                if not os.path.exists(srv_lnk):
                    # object does not exist _or_ is a broken link
                    if not os.path.islink(srv_lnk):
                        # if it truly does not exist, make a link
                        os.symlink(self.lib_path, srv_lnk)
                    else:
                        # Link exists and it is broken, make new one
                        os.unlink(srv_lnk)
                        os.symlink(self.lib_path, srv_lnk)
                ipautil.run(["/bin/systemctl", "--system", "daemon-reload"])
            except:
                pass
        else:
            self.__enable(instance_name)

    def disable(self, instance_name=""):
        elements = self.systemd_name.split("@")
        if instance_name != "" and len(elements) > 1:
            # Remove instance, we need to do following:
            #  Remove link from /etc/systemd/system/<service>.target.wants/<service>@<instance_name>.service
            #  to /lib/systemd/system/<service>@.service
            srv_tgt = os.path.join(self.SYSTEMD_ETC_PATH, self.SYSTEMD_SRV_TARGET % (elements[0]))
            srv_lnk = os.path.join(srv_tgt, self.service_instance(instance_name))
            try:
                if ipautil.dir_exists(srv_tgt):
                    if os.path.islink(srv_lnk):
                        os.unlink(srv_lnk)
                ipautil.run(["/bin/systemctl", "--system", "daemon-reload"])
            except:
                pass
        else:
            self.__disable(instance_name)

    def __enable(self, instance_name=""):
        try:
            ipautil.run(["/bin/systemctl", "enable", self.service_instance(instance_name)])
        except ipautil.CalledProcessError, e:
            pass

    def __disable(self, instance_name=""):
        try:
            ipautil.run(["/bin/systemctl", "disable", self.service_instance(instance_name)])
        except ipautil.CalledProcessError, e:
            pass

    def install(self):
        self.enable()

    def remove(self):
        self.disable()
