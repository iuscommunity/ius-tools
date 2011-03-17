"""
This bootstrap module should be used to setup parts of the versiontracker plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

from pkg_resources import get_distribution
from cement.core.namespace import CementNamespace, register_namespace

VERSION = get_distribution('iustools.versiontracker').version

# Setup the 'versiontracker' namespace object
versiontracker = CementNamespace(
    label='versiontracker', 
    description='Versiontracker Plugin for Iustools',
    version=VERSION,
    controller='VersiontrackerController',
    provider='iustools'
    )

# Directory where Package Configuration is kept
versiontracker.config['pkg_dir'] = '/usr/share/ossvt/pkgs/'
versiontracker.config['name'] = False

# Layout for output
versiontracker.config['layout'] = '%-30s %-15s %-15s %s'
versiontracker.config['layout_titles'] = ('name', 'ius ver', 'upstream ver', 'status')

# Officialize and register the namespace
register_namespace(versiontracker)

