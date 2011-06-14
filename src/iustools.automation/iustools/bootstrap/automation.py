"""
This bootstrap module should be used to setup parts of the automation plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

from pkg_resources import get_distribution
from cement.core.namespace import CementNamespace, register_namespace

VERSION = get_distribution('iustools.automation').version

# Setup the 'automation' namespace object
automation = CementNamespace(
    label='automation', 
    description='Automation Plugin for Iustools',
    version=VERSION,
    controller='AutomationController',
    provider='iustools'
    )

# Add a config option to the automation namespace.  This is effectively the
# default setting for the config option.  Overridden by config files, and then
# cli options.
automation.config['foo'] = 'bar'

# Add a cli option to the automation namespace.  This overrides the 
# coresponding config option if passed
automation.options.add_option('-F', '--foo', action='store', dest='foo',
    help='example automation option')

# Officialize and register the namespace
register_namespace(automation)

