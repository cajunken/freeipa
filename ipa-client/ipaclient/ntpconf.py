# Authors: Karl MacMillan <kmacmillan@redhat.com>
#
# Copyright (C) 2007  Red Hat
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
#

from ipapython import ipautil
from ipapython import services as ipaservices
import shutil
import os

ntp_conf = """# Permit time synchronization with our time source, but do not
# permit the source to query or modify the service on this system.
restrict default kod nomodify notrap nopeer noquery
restrict -6 default kod nomodify notrap nopeer noquery

# Permit all access over the loopback interface.  This could
# be tightened as well, but to do so would effect some of
# the administrative functions.
restrict 127.0.0.1
restrict -6 ::1

# Hosts on local network are less restricted.
#restrict 192.168.1.0 mask 255.255.255.0 nomodify notrap

# Use public servers from the pool.ntp.org project.
# Please consider joining the pool (http://www.pool.ntp.org/join.html).
server $SERVER

#broadcast 192.168.1.255 key 42		# broadcast server
#broadcastclient			# broadcast client
#broadcast 224.0.1.1 key 42		# multicast server
#multicastclient 224.0.1.1		# multicast client
#manycastserver 239.255.254.254		# manycast server
#manycastclient 239.255.254.254 key 42	# manycast client

# Undisciplined Local Clock. This is a fake driver intended for backup
# and when no outside source of synchronized time is available.
server	127.127.1.0	# local clock
#fudge	127.127.1.0 stratum 10

# Drift file.  Put this in a directory which the daemon can write to.
# No symbolic links allowed, either, since the daemon updates the file
# by creating a temporary in the same directory and then rename()'ing
# it to the file.
driftfile /var/lib/ntp/drift

# Key file containing the keys and key identifiers used when operating
# with symmetric key cryptography.
keys /etc/ntp/keys

# Specify the key identifiers which are trusted.
#trustedkey 4 8 42

# Specify the key identifier to use with the ntpdc utility.
#requestkey 8

# Specify the key identifier to use with the ntpq utility.
#controlkey 8
"""

ntp_sysconfig = """# Drop root to id 'ntp:ntp' by default.
OPTIONS="-x -u ntp:ntp -p /var/run/ntpd.pid"

# Set to 'yes' to sync hw clock after successful ntpdate
SYNC_HWCLOCK=yes

# Additional options for ntpdate
NTPDATE_OPTIONS=""
"""
ntp_step_tickers = """# Use IPA-provided NTP server for initial time
$SERVER
"""
def __backup_config(path, fstore = None):
    if fstore:
        fstore.backup_file(path)
    else:
        shutil.copy(path, "%s.ipasave" % (path))

def __write_config(path, content):
    fd = open(path, "w")
    fd.write(content)
    fd.close()

def config_ntp(server_fqdn, fstore = None, sysstore = None):
    path_step_tickers = "/etc/ntp/step-tickers"
    path_ntp_conf = "/etc/ntp.conf"
    path_ntp_sysconfig = "/etc/sysconfig/ntpd"
    sub_dict = { }
    sub_dict["SERVER"] = server_fqdn

    nc = ipautil.template_str(ntp_conf, sub_dict)
    config_step_tickers = False


    if os.path.exists(path_step_tickers):
        config_step_tickers = True
        ns = ipautil.template_str(ntp_step_tickers, sub_dict)
        __backup_config(path_step_tickers, fstore)
        __write_config(path_step_tickers, ns)
        ipaservices.restore_context(path_step_tickers)

    if sysstore:
        module = 'ntp'
        sysstore.backup_state(module, "enabled", ipaservices.knownservices.ntpd.is_enabled())
        if config_step_tickers:
            sysstore.backup_state(module, "step-tickers", True)

    __backup_config(path_ntp_conf, fstore)
    __write_config(path_ntp_conf, nc)
    ipaservices.restore_context(path_ntp_conf)

    __backup_config(path_ntp_sysconfig, fstore)
    __write_config(path_ntp_sysconfig, ntp_sysconfig)
    ipaservices.restore_context(path_ntp_sysconfig)

    # Set the ntpd to start on boot
    ipaservices.knownservices.ntpd.enable()

    # Restart ntpd
    ipaservices.knownservices.ntpd.restart()


def synconce_ntp(server_fqdn):
    """
    Syncs time with specified server using ntpd.
    Primarily designed to be used before Kerberos setup
    to get time following the KDC time

    Returns True if sync was successful
    """
    ntpd = '/usr/sbin/ntpd'
    if not os.path.exists(ntpd):
        return False

    tmp_ntp_conf = ipautil.write_tmp_file('server %s' % server_fqdn)
    try:
        ipautil.run([ntpd, '-qgc', tmp_ntp_conf.name])
        return True
    except ipautil.CalledProcessError:
        return False


class NTPConfigurationError(Exception):
    pass

class NTPConflictingService(NTPConfigurationError):
    def __init__(self, message='', conflicting_service=None):
        super(NTPConflictingService, self).__init__(self, message)
        self.conflicting_service = conflicting_service

def check_timedate_services():
    """
    System may contain conflicting services used for time&date synchronization.
    As IPA server/client supports only ntpd, make sure that other services are
    not enabled to prevent conflicts. For example when both chronyd and ntpd
    are enabled, systemd would always start only chronyd to manage system
    time&date which would make IPA configuration of ntpd ineffective.

    Reference links:
      https://fedorahosted.org/freeipa/ticket/2974
      http://fedoraproject.org/wiki/Features/ChronyDefaultNTP
    """
    for service in ipaservices.timedate_services:
        if service == 'ntpd':
            continue
        # Make sure that the service is not enabled
        service = ipaservices.service(service)
        if service.is_enabled() or service.is_running():
            raise NTPConflictingService(conflicting_service=service.service_name)

def force_ntpd(statestore):
    """
    Force ntpd configuration and disable and stop any other conflicting
    time&date service
    """
    for service in ipaservices.timedate_services:
        if service == 'ntpd':
            continue
        service = ipaservices.service(service)
        enabled = service.is_enabled()
        running = service.is_running()

        if enabled or running:
            statestore.backup_state(service.service_name, 'enabled', enabled)
            statestore.backup_state(service.service_name, 'running', running)

            if running:
                service.stop()

            if enabled:
                service.disable()

def restore_forced_ntpd(statestore):
    """
    Restore from --force-ntpd installation and enable/start service that were
    disabled/stopped during installation
    """
    for service in ipaservices.timedate_services:
        if service == 'ntpd':
            continue
        if statestore.has_state(service):
            service = ipaservices.service(service)
            enabled = statestore.restore_state(service.service_name, 'enabled')
            running = statestore.restore_state(service.service_name, 'running')
            if enabled:
                service.enable()
            if running:
                service.start()
