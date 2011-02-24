"""
This bootstrap module should be used to setup parts of the ircbot plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

from pkg_resources import get_distribution
from cement.core.namespace import CementNamespace, register_namespace

VERSION = get_distribution('iustools.ircbot').version

# Setup the 'ircbot' namespace object
ircbot = CementNamespace(
    label='ircbot', 
    description='IRC Bot Plugin for IUS Community Project Tools',
    version=VERSION,
    controller='IRCBotController',
    provider='iustools'
    )

# default config options
ircbot.config['server'] = 'irc.freenode.net'
ircbot.config['port'] = 6667
ircbot.config['channel'] = 'iuscommunity'
ircbot.config['nick'] = 'iusbot'

# command line options
ircbot.options.add_option('--irc-channel', action='store', dest='channel',
    help='the irc channel to join')
ircbot.options.add_option('--irc-nick', action='store', dest='nick',
    help='the irc nick to register as')

# Officialize and register the namespace
register_namespace(ircbot)

