"""
This bootstrap module should be used to setup parts of the example plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

from pkg_resources import get_distribution
from cement.core.namespace import CementNamespace, register_namespace

VERSION = get_distribution('iustools.example').version

# Setup the 'example' namespace object
example = CementNamespace(
    label='example', 
    description='Example Plugin for Iustools',
    version=VERSION,
    controller='ExampleController',
    provider='iustools'
    )

# Add a config option to the example namespace.  This is effectively the
# default setting for the config option.  Overridden by config files, and then
# cli options.
example.config['foo'] = 'bar'

# Add a cli option to the example namespace.  This overrides the 
# coresponding config option if passed
example.options.add_option('-F', '--foo', action='store', dest='foo',
    help='example example option')

# Officialize and register the namespace
register_namespace(example)

