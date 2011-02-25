"""
The bootstrap module should be used to setup parts of your application
that need to exist before all controllers are loaded.  It is best used to 
define hooks, setup namespaces, and the like.  The root namespace is 
already bootstrapped by Cement, however you can extend that functionality
by importing additional bootstrap files here.
"""

from cement.core.opt import init_parser
from cement.core.hook import register_hook

# Register root options
@register_hook()
def options_hook(*args, **kwargs):
    # This hook allows us to append options to the root namespace
    root_options = init_parser()
    root_options.add_option('--json', action='store_true',
        dest='enable_json', default=None, 
        help='render output as json (CLI-API)')
    root_options.add_option('--debug', action='store_true',
        dest='debug', default=None, help='toggle debug output')
    root_options.add_option('--quiet', action='store_true',
        dest='quiet', default=None, help='disable console logging')
    root_options.add_option('-s', '--server', action='store', dest='server',
        help='server fqdn/ip to connect to')
    root_options.add_option('-p', '--port', action='store', dest='port',
        help='the server port to connect on')
    root_options.add_option('--pid-file', action='store', dest='pid_file',
        help='path to pid file')
    root_options.add_option('--run-as', action='store', dest='process_user',
        help='user to run as (where applicable)')
    root_options.add_option('--daemonize', action='store_true',
        dest='daemonize', default=None, help="daemonize the process")   
    return ('root', root_options)

# Import all additional (non-plugin) bootstrap libraries here    
# 
#   from iustools.bootstrap import example
#
    