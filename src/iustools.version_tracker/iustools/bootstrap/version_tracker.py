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

# Plugin options
version_tracker.config['launchpad'] = None
version_tracker.options.add_option('--launchpad', action='store_true', dest='launchpad',
    help='if you wish the tool to add Launchpad tickets', default=None)
version_tracker.config['email'] = None
version_tracker.options.add_option('--email', action='store_true', dest='email',
    help='send output in email to configured recipients', default=None)

# Configuration for --email Email notifications
version_tracker.config['fromaddr'] = 'nobody@example.com'
version_tracker.config['toaddr'] = 'nobody@example.com'
version_tracker.config['subject'] = '[ius-community] IUS Version Tracker'
