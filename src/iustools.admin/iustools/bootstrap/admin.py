"""
This bootstrap module should be used to setup parts of the admin plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

from pkg_resources import get_distribution
from cement.core.namespace import CementNamespace, register_namespace

VERSION = get_distribution('iustools.admin').version

# Setup the 'admin' namespace object
admin = CementNamespace(
    label='admin', 
    description='Admin Plugin for Iustools',
    version=VERSION,
    controller='AdminController',
    provider='iustools'
    )

# Add a config option to the admin namespace.  This is effectively the
# default setting for the config option.  Overridden by config files, and then
# cli options.
admin.config['managed_tags'] = ['testing', 'stable', 'dev']
admin.config['managed_releases'] = ['el5', 'el5.6.z', 'el6', 'el6.0.z', 'el6.1.z', 'el6.2.z']
admin.config['managed_archs'] = ['i386', 'x86_64']
admin.config['repo_base_path'] = '~/ius-repo'
admin.config['remote_rsync_path'] = '~/ius-repo'
admin.config['remote_exclude'] = "[0-9]\.[0-9]"
admin.config['internal_remote_rsync_path'] = False
admin.config['internal_remote_exclude'] = False
admin.config['rpm_binpath'] = '/bin/rpm'
admin.config['rsync_binpath'] = '/usr/bin/rsync'
admin.config['createrepo_binpath'] = '/usr/bin/createrepo'
admin.config['createrepo_opts'] = '--database --checksum md5 --simple-md-filenames'
admin.config['yumarch_binpath'] = '/usr/bin/yum-arch'
admin.config['repoview_binpath'] = '/usr/bin/repoview'
admin.config['gpg_passphrase'] = ''
admin.config['announce_email'] = 'announce@example.com'
admin.config['smtp_from'] = 'noreply@example.com'
admin.config['smtp_host'] = 'localhost'
admin.config['smtp_port'] = 25
admin.config['smtp_user'] = ''
admin.config['smtp_password'] = ''
admin.config['smtp_tls'] = False
admin.config['smtp_keyfile'] = '/etc/pki/tls/private/localhost.key'
admin.config['smtp_certfile'] = '/etc/pki/tls/certs/localhost.crt'
admin.config['smtp_subject_prefix'] = '[ius] '
admin.config['gpg_key_file_path'] = '/usr/share/ius-tools/IUS-COMMUNITY-GPG-KEY'
admin.config['eua_file_path'] = '/usr/share/ius-tools/IUS-COMMUNITY-EUA'

# Add a cli option to the admin namespace.  This overrides the 
# coresponding config option if passed
admin.options.add_option('--tag', action='store', dest='tag_label',
    help='tag label')
admin.options.add_option('--sign', action='store_true', dest='sign',
    help='sign stable packages')
admin.options.add_option('--clean', action='store_true', dest='clean',
    help='clean destination repo before creation (used with gen-repo)')
admin.options.add_option('--delete', action='store_true', dest='delete',
    help='delete old files from remote destination')
admin.options.add_option('--passphrase', action='store', metavar='STR', 
    dest='gpg_passphrase', help='gpg key passphrase')
    
# Officialize and register the namespace
register_namespace(admin)



