# Authors:
#   Petr Viktorin <pviktori@redhat.com>
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

"""Common tasks for FreeIPA integration tests"""

import os
import textwrap
import re
import collections
import itertools

from ipapython import ipautil
from ipapython.ipa_log_manager import log_mgr
from ipatests.test_integration.config import env_to_script

log = log_mgr.get_logger(__name__)


def prepare_host(host):
    env_filename = os.path.join(host.config.test_dir, 'env.sh')
    host.collect_log(env_filename)
    host.mkdir_recursive(host.config.test_dir)
    host.put_file_contents(env_filename, env_to_script(host.to_env()))


def apply_common_fixes(host):
    fix_etc_hosts(host)
    fix_hostname(host)
    fix_resolv_conf(host)


def backup_file(host, filename):
    if host.file_exists(filename):
        backupname = os.path.join(host.config.test_dir, 'file_backup',
                                  filename.lstrip('/'))
        host.mkdir_recursive(os.path.dirname(backupname))
        host.run_command(['cp', '-af', filename, backupname])
        return True
    else:
        rmname = os.path.join(host.config.test_dir, 'file_remove')
        host.run_command('echo %s >> %s' % (
            ipautil.shell_quote(filename),
            ipautil.shell_quote(rmname)))
        contents = host.get_file_contents(rmname)
        host.mkdir_recursive(os.path.dirname(rmname))
        return False


def fix_etc_hosts(host):
    backup_file(host, '/etc/hosts')
    contents = host.get_file_contents('/etc/hosts')
    # Remove existing mentions of the host's FQDN, short name, and IP
    contents = re.sub('\s%s(\s|$)' % re.escape(host.hostname), ' ', contents,
                      flags=re.MULTILINE)
    contents = re.sub('\s%s(\s|$)' % re.escape(host.shortname), ' ', contents,
                      flags=re.MULTILINE)
    contents = re.sub('^%s.*' % re.escape(host.ip), '', contents,
                      flags=re.MULTILINE)
    # Add the host's info again
    contents += '\n%s %s %s\n' % (host.ip, host.hostname, host.shortname)
    log.debug('Writing the following to /etc/hosts:\n%s', contents)
    host.put_file_contents('/etc/hosts', contents)


def fix_hostname(host):
    backup_file(host, '/etc/hostname')
    host.put_file_contents('/etc/hostname', host.hostname + '\n')
    host.run_command(['hostname', host.hostname])

    backupname = os.path.join(host.config.test_dir, 'backup_hostname')
    host.run_command('hostname > %s' % ipautil.shell_quote(backupname))


def fix_resolv_conf(host):
    backup_file(host, '/etc/resolv.conf')
    lines = host.get_file_contents('/etc/resolv.conf').splitlines()
    lines = ['#' + l if l.startswith('nameserver') else l for l in lines]
    for other_host in host.domain.hosts:
        if other_host.role in ('master', 'replica'):
            lines.append('nameserver %s' % other_host.ip)
    contents = '\n'.join(lines)
    log.debug('Writing the following to /etc/resolv.conf:\n%s', contents)
    host.put_file_contents('/etc/resolv.conf', contents)


def unapply_fixes(host):
    restore_files(host)
    restore_hostname(host)

    # Clean up the test directory
    host.run_command(['rm', '-rvf', host.config.test_dir])


def restore_files(host):
    backupname = os.path.join(host.config.test_dir, 'file_backup')
    rmname = os.path.join(host.config.test_dir, 'file_remove')
    host.run_command('cp -arvf %s/* /' % ipautil.shell_quote(backupname),
                     raiseonerr=False)
    host.run_command(['xargs', '-d', r'\n', '-a', rmname, 'rm', '-vf'],
                     raiseonerr=False)
    host.run_command(['rm', '-rvf', backupname, rmname], raiseonerr=False)


def restore_hostname(host):
    backupname = os.path.join(host.config.test_dir, 'backup_hostname')
    try:
        hostname = host.get_file_contents(backupname)
    except IOError:
        log.debug('No hostname backed up on %s' % host.hostname)
    else:
        host.run_command(['hostname', hostname.strip()])
        host.run_command(['rm', backupname])


def enable_replication_debugging(host):
    log.info('Enable LDAP replication logging')
    logging_ldif = textwrap.dedent("""
        dn: cn=config
        changetype: modify
        replace: nsslapd-errorlog-level
        nsslapd-errorlog-level: 8192
        """)
    host.run_command(['ldapmodify', '-x',
                      '-D', str(host.config.dirman_dn),
                      '-w', host.config.dirman_password],
                     stdin_text=logging_ldif)


def install_master(host):
    host.collect_log('/var/log/ipaserver-install.log')
    host.collect_log('/var/log/ipaclient-install.log')
    inst = host.domain.realm.replace('.', '-')
    host.collect_log('/var/log/dirsrv/slapd-%s/errors' % inst)
    host.collect_log('/var/log/dirsrv/slapd-%s/access' % inst)

    apply_common_fixes(host)

    host.run_command(['ipa-server-install', '-U',
                      '-r', host.domain.name,
                      '-p', host.config.dirman_password,
                      '-a', host.config.admin_password,
                      '--setup-dns',
                      '--forwarder', host.config.dns_forwarder])

    enable_replication_debugging(host)

    kinit_admin(host)


def install_replica(master, replica, setup_ca=True):
    replica.collect_log('/var/log/ipareplica-install.log')
    replica.collect_log('/var/log/ipareplica-conncheck.log')

    apply_common_fixes(replica)

    master.run_command(['ipa-replica-prepare',
                        '-p', replica.config.dirman_password,
                        '--ip-address', replica.ip,
                        replica.hostname])
    replica_bundle = master.get_file_contents(
        '/var/lib/ipa/replica-info-%s.gpg' % replica.hostname)
    replica_filename = os.path.join(replica.config.test_dir,
                                    'replica-info.gpg')
    replica.put_file_contents(replica_filename, replica_bundle)
    args = ['ipa-replica-install', '-U',
            '--setup-ca',
            '-p', replica.config.dirman_password,
            '-w', replica.config.admin_password,
            '--ip-address', replica.ip,
            replica_filename]
    if setup_ca:
        args.append('--setup-ca')
    replica.run_command(args)

    enable_replication_debugging(replica)

    kinit_admin(replica)

def install_client(master, client):
    client.collect_log('/var/log/ipaclient-install.log')

    apply_common_fixes(client)

    client.run_command(['ipa-client-install', '-U',
                        '--domain', client.domain.name,
                        '--realm', client.domain.realm,
                        '-p', client.config.admin_name,
                        '-w', client.config.admin_password,
                        '--server', master.hostname])

    kinit_admin(client)


def connect_replica(master, replica):
    kinit_admin(replica)
    replica.run_command(['ipa-replica-manage', 'connect', master.hostname])


def disconnect_replica(master, replica):
    kinit_admin(replica)
    replica.run_command(['ipa-replica-manage', 'disconnect', master.hostname])


def kinit_admin(host):
    host.run_command(['kinit', 'admin'],
                      stdin_text=host.config.admin_password)


def uninstall_master(host):
    host.collect_log('/var/log/ipaserver-uninstall.log')

    host.run_command(['ipa-server-install', '--uninstall', '-U'],
                     raiseonerr=False)
    unapply_fixes(host)


def uninstall_client(host):
    host.collect_log('/var/log/ipaclient-uninstall.log')

    host.run_command(['ipa-client-install', '--uninstall', '-U'],
                     raiseonerr=False)
    unapply_fixes(host)


def get_topo(name_or_func):
    """Get a topology function by name

    A topology function receives a master and list of replicas, and yields
    (parent, child) pairs, where "child" should be installed from "parent"
    (or just connected if already installed)

    If a callable is given instead of name, it is returned directly
    """
    if callable(name_or_func):
        return name_or_func
    return topologies[name_or_func]


def _topo(name):
    """Decorator that registers a function in topologies under a given name"""
    def add_topo(func):
        topologies[name] = func
        return func
    return add_topo
topologies = collections.OrderedDict()


@_topo('star')
def star_topo(master, replicas):
    r"""All replicas are connected to the master

          Rn R1 R2
           \ | /
        R7-- M -- R3
           / | \
          R6 R5 R4
    """
    for replica in replicas:
        yield master, replica


@_topo('line')
def line_topo(master, replicas):
    r"""Line topology

          M
           \
           R1
            \
            R2
             \
             R3
              \
              ...
    """
    for replica in replicas:
        yield master, replica
        master = replica


@_topo('complete')
def complete_topo(master, replicas):
    r"""Each host connected to each other host

          M--R1
          |\/|
          |/\|
         R3-R4
    """
    for replica in replicas:
        yield master, replica
    for replica1, replica2 in itertools.combinations(replicas, 2):
        yield replica1, replica2


@_topo('tree')
def tree_topo(master, replicas):
    r"""Binary tree topology

             M
            / \
           /   \
          R1   R2
         /  \  / \
        R3 R4 R5 R6
       /
      R7 ...

    """
    replicas = list(replicas)

    def _masters():
        for host in [master] + replicas:
            yield host
            yield host

    for parent, child in zip(_masters(), replicas):
        yield parent, child


@_topo('tree2')
def tree2_topo(master, replicas):
    r"""First replica connected directly to master, the rest in a line

          M
         / \
        R1 R2
            \
            R3
             \
             R4
              \
              ...

    """
    if replicas:
        yield master, replicas[0]
    for replica in replicas[1:]:
        yield master, replica
        master = replica


def install_topo(topo, master, replicas, clients,
                 skip_master=False, setup_replica_cas=True):
    """Install IPA servers and clients in the given topology"""
    replicas = list(replicas)
    installed = {master}
    if not skip_master:
        install_master(master)
    for parent, child in get_topo(topo)(master, replicas):
        if child in installed:
            log.info('Connecting replica %s to %s' % (parent, child))
            connect_replica(parent, child)
        else:
            log.info('Installing replica %s from %s' % (parent, child))
            install_replica(parent, child, setup_ca=setup_replica_cas)
        installed.add(child)
    install_clients([master] + replicas, clients)


def install_clients(servers, clients):
    """Install IPA clients, distributing them among the given servers"""
    for server, client in itertools.izip(itertools.cycle(servers), clients):
        log.info('Installing client %s on %s' % (server, client))
        install_client(server, client)
