
import re
import socket
from time import sleep

from cement.core.log import get_logger

log = get_logger(__name__)

class IRC(object):
    def __init__(self, server, port, channel, nick, recv_bytes=512):
        self.server = server
        self.port = port
        self.channel = channel
        self.nick = nick
        self.recv_bytes = recv_bytes

        if not self.channel.startswith('#'):
            self.channel = '#%s' % self.channel
        
    def connect(self):
        while True:
            try:
                self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.ircsock.connect((self.server, int(self.port)))
                self.ircsock.send("USER %s %s %s :IUS IRC Bot.\n" % \
                                (self.nick, self.nick, self.nick))
                self.ircsock.send("NICK "+ self.nick +"\n")
                self.join_channel(self.channel)
                return self.ircsock
            except socket.error, e:
                log.error("Caught socket.error: %s. Sleeping 30 seconds..." % e)
                sleep(30)

    def poll(self, count=2048):
        """
        Poll the IRC stream for data, only return anything if the msg
        is relevant for the bot to handle.
        
        Returns:
        
            tuple - (from_nick, from_chan, msg, dest).  dest is the expected
                    destination of the reply (either a channel, or a PM to
                    a nick)
                    
            
        """
        data = ''
        try:
            data = self.ircsock.recv(int(self.recv_bytes)).strip('\n\r')
        except socket.error, e:
            log.error("Caught socket.error: %s" % e)
            # retry
            try:
                self.connect()
                data = self.ircsock.recv(int(self.recv_bytes)).strip('\n\r')
            except:
                pass

        res = None
        
        if re.search("PING :", data):
            self.pong()
            res = None
            
        elif re.search("PRIVMSG", data):
            # Format is:
            # :<nick>!<user@host> PRIVMSG #channel :msg
            #
            # however direct PM's, self.nick is in place of #channel
            #

            m = re.match(':(.*)\!(.*)[\s](.*)[\s](.*)[\s]:(.*)', data)
            if m:
                from_nick = m.groups()[0]
                from_user = m.groups()[1]
                from_chan = m.groups()[3]                    
                msg = m.groups()[4]
                
                if from_chan == self.nick:
                    dest = from_nick
                else:
                    dest = from_chan
                    
                if msg.startswith(self.nick):
                    msg = re.sub(self.nick, '', msg).lstrip(':, ')
                
                res = (from_nick, from_chan, msg, dest)                

        if res:
            log.debug("ircbot received message: from_nick='%s' from_chan='%s' msg='%s' dest='%s'" % res)
        return res
        
    def quit(self):
        log.warn('quiting...')
        self.ircsock.close()

    def join_channel(self, channel):
        log.info('joining channel %s' % channel)
        try:
            self.ircsock.send("JOIN "+ channel +"\n")
        except socket.error, e:
            log.error("Caught socket.error: %s" % e)
            try:
                # retry - XXX FIX ME: this can result in a maximum recursion
                self.connect()
                self.ircsock.send("JOIN "+ channel +"\n")
            except:
                pass

            
    def ping(self):
        log.debug('sending keep alive ping to server')
        try:
            self.ircsock.send("PING\n")
        except socket.error, e:
            log.error("Caught socket.error: %s" % e)
            try:
                # retry
                self.connect()
                self.ircsock.send("PING\n")
            except:
                pass

    def pong(self):
        log.debug('sending pong response')
        try:
            self.ircsock.send("PONG :pingis\n")
        except socket.error, e:
            log.error("Caught socket.error: %s" % e)
            try:
                # retry
                self.connect()
                self.ircsock.send("PONG :pingis\n")
            except:
                pass
                
    def send(self, nick_or_channel, msg):
        log.debug('sending msg to %s' % nick_or_channel)
        try:
            self.ircsock.send("PRIVMSG %s :%s\n" % (nick_or_channel, msg))
        except socket.error, e:
            log.error("Caught socket.error: %s" % e)
            try:
                # retry
                self.connect()
                self.ircsock.send("PRIVMSG %s :%s\n" % (nick_or_channel, msg))
            except:
                pass
            
    def send_to_channel(self, msg):
        self.send(self.channel, msg)
