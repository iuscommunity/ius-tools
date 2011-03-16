"""
This bootstrap module should be used to setup parts of the getspec plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

from pkg_resources import get_distribution
from cement.core.namespace import CementNamespace, register_namespace

VERSION = get_distribution('iustools.getspec').version

# Setup the 'getspec' namespace object
getspec = CementNamespace(
    label='getspec', 
    description='Getspec Plugin for Iustools',
    version=VERSION,
    controller='GetspecController',
    provider='iustools'
    )

# Officialize and register the namespace
register_namespace(getspec)

