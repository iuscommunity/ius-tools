"""
This bootstrap module should be used to setup parts of the ircbot plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

import os
import json
import re
from urllib2 import urlopen, HTTPError, URLError

from time import sleep
from pkg_resources import get_distribution
from datetime import datetime
from launchpadlib.launchpad import Launchpad

from cement import namespaces
from cement.core.namespace import CementNamespace, register_namespace
from cement.core.namespace import get_config
from cement.core.testing import simulate
from cement.core.controller import run_controller_command
from cement.core.hook import define_hook, register_hook

from iustools import irc_commands
from iustools.core.exc import IUSToolsArgumentError

VERSION = get_distribution('iustools.ircbot').version

define_hook('ircbot_process_hook')

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
ircbot.config['process_user'] = 'iusdaemon'
ircbot.config['pid_file'] = '/var/run/ius-tools/ircbot.pid'
ircbot.config['bitly_baseurl'] = 'http://api.bit.ly/v3/shorten/'
ircbot.config['bitly_user'] = 'iuscommunity'
ircbot.config['bitly_apikey'] = None

# command line options
ircbot.options.add_option('--irc-channel', action='store', dest='channel',
    help='the irc channel to join')
ircbot.options.add_option('--irc-nick', action='store', dest='nick',
    help='the irc nick to register as')
ircbot.options.add_option('--run-once', action='store', dest='run_once',
    help='just run a specific ircbot process hook once')

# Officialize and register the namespace
register_namespace(ircbot)

@register_hook()
def post_options_hook(*args, **kw):
    config = get_config()
    if not os.path.exists(config['ircbot']['pid_file']):
        os.makedirs(config['ircbot']['pid_file'])

@register_hook(name='ircbot_process_hook')
def interactive_ircbot_process_hook(config, log, irc):
    """
    This process hook listens on the IRC channel, and responds to interactive
    requests.
    """
    while True:
        res = irc.poll()
        if res:
            log.debug('ircbot received message: %s %s %s' % res)
            (from_nick, from_chan, msg) = res
            if from_chan == irc.nick:
                dest = from_nick
            else:
                dest = from_chan
            
            args = msg.split() 
            cmd = args.pop(0) # first part of msg is command, rest args
            if cmd in irc_commands.keys():            
                # need to keep arg order
                args.insert(0, irc_commands[cmd]['func'])
                if irc_commands[cmd]['namespace'] != 'root':
                    args.insert(0, irc_commands[cmd]['namespace'])    
                args.insert(0, 'ius-tools')
            
                try:
                    # FIX ME: this is a bit of a hack
                    nam = namespaces[irc_commands[cmd]['namespace']]
                    nam.controller.cli_opts = None
                    nam.controller.cli_args = None
                    namespaces[irc_commands[cmd]['namespace']] = nam
                    (out_dict, out_txt) = simulate(args)
                    reply = out_dict['irc_data']
                except IUSToolsArgumentError, e:
                    reply = e.msg
                    out_dict = {}
                    
                # FIX ME: Need to consolidate all this .startswith('#') stuff
                
                # only send to user directly?
                if out_dict.has_key('irc_pm') and out_dict['irc_pm']:    
                    if dest.startswith('#'):
                        irc.send(from_chan, "%s: check your PM." % from_nick)
                        irc.send(from_nick, "%s" % reply)
                    else:
                        irc.send(from_nick, "%s" % reply)
                else:
                    if dest.startswith('#'):
                        irc.send(dest, "%s: %s" % (from_nick, reply))
                    else:
                        irc.send(dest, "%s" % reply)
            else:
                reply = "I don't understand that command."
                if dest.startswith('#'):
                    irc.send(dest, "%s: %s" % (from_nick, reply))
                else:
                    irc.send(dest, "%s" % reply)
        sleep(1)

@register_hook(name='ircbot_process_hook')
def new_bug_notify_ircbot_process_hook(config, log, irc):
    """
    Monitor LaunchPad for new bugs, and post to irc.
    """
    last_update = datetime.utcnow()
    while True:
        log.debug('checking LaunchPad for new bugs')
        now = datetime.utcnow()
        
        lp = Launchpad.login_anonymously('ius-tools', 'production')
        ius = lp.projects.search(text='ius')[0]
        tasks = ius.searchTasks()
        for task in tasks:
            if last_update < task.date_created.replace(tzinfo=None):
                bitly_url = "%s?format=json&longUrl=%s&login=%s&apiKey=%s" % (
                        config['ircbot']['bitly_baseurl'],
                        unicode(task.web_link),
                        config['ircbot']['bitly_user'],
                        config['ircbot']['bitly_apikey'],
                        )
                bitly_url = re.sub('\+', '%2b', bitly_url)
                
                res = urlopen(bitly_url)
                data = json.loads(res.read())
                short_url = data['data']['url']
                
                reply = "New %s - %s" % (task.title, short_url)
                irc.send_to_channel(reply)

        last_update = datetime.utcnow()
        sleep(30)
    
    