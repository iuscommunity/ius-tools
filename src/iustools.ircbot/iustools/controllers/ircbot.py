"""ircbot controller class to expose commands for iustools."""

from time import sleep

from cement.core.controller import CementController, expose
from cement.core.namespace import get_config
from cement.core.log import get_logger

from iustools.lib.ircbot import IRC

log = get_logger(__name__)
config = get_config()

class IRCBotController(CementController):
    @expose(namespace='ircbot')
    def default(self):
        irc = IRC(server=config['ircbot']['server'],
                  port=config['ircbot']['port'],
                  channel=config['ircbot']['channel'],
                  nick=config['ircbot']['nick'])
        irc.connect()
        
        while True:
            res = irc.poll()
            if res:
                (from_nick, from_chan, msg) = res
                if from_chan == irc.nick:
                    dest = from_nick
                else:
                    dest = from_chan
                irc.send(dest, "%s: blah" % from_nick)
            sleep(1)
            
        return dict()

