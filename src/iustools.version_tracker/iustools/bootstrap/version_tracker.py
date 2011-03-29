"""
This bootstrap module should be used to setup parts of the version_tracker plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

from pkg_resources import get_distribution
from cement.core.namespace import CementNamespace, register_namespace

VERSION = get_distribution('iustools.version_tracker').version

# Setup the 'version_tracker' namespace object
version_tracker = CementNamespace(
    label='version_tracker', 
    description='Version Tracker Plugin for IUS Tools',
    version=VERSION,
    controller='VersionTrackerController',
    provider='iustools'
    )

# Directory where Package Configuration is kept
version_tracker.config['pkg_dir'] = '/usr/share/ius-tools/version_tracker/pkgs/'
version_tracker.config['ius_baseurl'] = 'http://dl.iuscommunity.org/pub/ius'

# Layout for output
version_tracker.config['layout'] = '%-30s %-15s %-15s %s'
version_tracker.config['layout_titles'] = ('name', 'ius ver', 'upstream ver', 'status')
    
# Officialize and register the namespace
register_namespace(version_tracker)

