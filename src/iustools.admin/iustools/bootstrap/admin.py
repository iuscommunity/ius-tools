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
admin.config['repo_base_path'] = '~/ius-repo'
admin.config['remote_rsync_path'] = '~/ius-repo'


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
    
# Officialize and register the namespace
register_namespace(admin)



