"""ircbot controller class to expose commands for iustools."""

import os
import sys
import pwd
import signal
from time import sleep
from multiprocessing import Process

from cement import hooks, namespaces
from cement.core.controller import CementController
from cement.core.namespace import get_config
from cement.core.log import get_logger

from iustools import irc_commands
from iustools.core.controller import expose
from iustools.lib.ircbot import IRC
from iustools.lib.daemonize import daemonize

log = get_logger(__name__)
config = get_config()
child_processes = {}

def signal_handler(signum, frame):
    log.warn('Caught signal %s, shutting down clean...' % signum)
    for c in child_processes:
        if child_processes[c]['process'].is_alive():
            child_processes[c]['process'].terminate()
    sys.exit()
    
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


class IRCBotController(CementController):
    @expose(namespace='ircbot', is_hidden=True)
    def default(self):
        u = pwd.getpwnam(config['ircbot']['process_user'])
        log.debug('setting process uid(%s) and gid(%s)' % (u.pw_uid, u.pw_gid))
        os.chown(os.path.dirname(config['ircbot']['pid_file']), 
                 u.pw_uid, u.pw_gid)
        os.chown(config['log_file'], u.pw_uid, u.pw_gid)
        os.setgid(u.pw_gid)
        os.setuid(u.pw_uid)

        if self.cli_opts.daemonize:
            config['output_handler'] = None
            daemonize()
            
        irc = IRC(server=config['ircbot']['server'],
                  port=config['ircbot']['port'],
                  channel=config['ircbot']['channel'],
                  nick=config['ircbot']['nick'])
        irc.connect()
        
        # just run a single process hook, or all
        hook_name = self.cli_opts.run_once or 'all'
        
        # note: cement hooks are in the fashion (weight, name, <func>)
        for hook in hooks['ircbot_process_hook']:
            if hook_name == 'all' or hook_name == hook[1]:
                log.debug("adding ircbot process hook '%s'" % hook[1])

                p = Process(target=hook[2], args=[config, log, irc])
                p.start()

                log.debug("spawned ircbot process '%s' (pid: %s)" % \
                        (hook[1], p.pid))
                        
                child_processes[hook[1]] = dict(func=hook[2], process=p)
                
        while True:
            for c in child_processes:
                if not child_processes[c]['process'].is_alive():
                    process = child_processes[c]['process']
                    log.error("ircbot child process %s died" % process.pid)
                    process = Process(target=child_processes[c]['func'], 
                                      args=[config, log, irc])
                    process.start()
                    child_processes[c]['process'] = process
                    log.debug("respawned ircbot process '%s' (pid: %s)" % \
                            (c, process.pid))
                        
            sleep(1)
            
        return dict()

    @expose(namespace='ircbot', irc_command='.help', is_hidden=True)
    def available_commands(self):
        for c in irc_commands.keys():
            print c
        irc_data = "Available Commands: %s" % ' '.join(irc_commands.keys())
        return dict(irc_pm=True, irc_data=irc_data)
        
    @expose(namespace='root', irc_command='.whoowns')
    def whoowns(self):
        try:
            pkg = self.cli_args[1]
            out_txt = "derks owns %s" % pkg
        except IndexError, e:
            out_txt = "first argument should be a package name."
        
        print out_txt
        return dict(irc_data=out_txt)
        