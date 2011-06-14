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
admin.config['foo'] = 'bar'

# Add a cli option to the admin namespace.  This overrides the 
# coresponding config option if passed
admin.options.add_option('-F', '--foo', action='store', dest='foo',
    help='example admin option')

# Officialize and register the namespace
register_namespace(admin)

