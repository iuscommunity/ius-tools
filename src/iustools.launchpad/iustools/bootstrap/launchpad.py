"""
This bootstrap module should be used to setup parts of the launchpad plugin
that need to exist before all controllers are loaded.  It is best used to 
define/register hooks, setup namespaces, and the like.  

"""

import re
from time import sleep
from pkg_resources import get_distribution
from launchpadlib.launchpad import Launchpad

from cement.core.namespace import CementNamespace, register_namespace
from cement.core.hook import register_hook

from iustools.lib.bitly import shorten_url


VERSION = get_distribution('iustools.launchpad').version

# Setup the 'launchpad' namespace object
launchpad = CementNamespace(
    label='launchpad', 
    description='LaunchPad Plugin for Iustools',
    version=VERSION,
    controller='LaunchPadController',
    provider='iustools'
    )

# Add a config option to the launchpad namespace.  This is effectively the
# default setting for the config option.  Overridden by config files, and then
# cli options.
launchpad.config['foo'] = 'bar'

# Add a cli option to the launchpad namespace.  This overrides the 
# coresponding config option if passed
launchpad.options.add_option('-F', '--foo', action='store', dest='foo',
    help='example launchpad option')

# Officialize and register the namespace
register_namespace(launchpad)


@register_hook(name='ircbot_process_hook')
def new_bug_notify_ircbot_process_hook(config, log, irc):
    """
    Monitor LaunchPad for new bugs, and post to irc.
    """

    lp_ids = []
    first_run = True

    while True:
        log.debug('checking LaunchPad for new bugs')
        
        lp = Launchpad.login_anonymously('ius-tools', 'production')
        ius = lp.projects.search(text='ius')[0]
        tasks = ius.searchTasks()

        for task in tasks:
            bugid = task.bug.id
            
            if first_run and bugid not in lp_ids:
                # just append all ids to the list
                log.debug('Adding %s to known ids' % bugid)
                lp_ids.append(bugid)

            elif not first_run and bugid not in lp_ids:
                # if not first run post to channel
                url = shorten_url(unicode(task.web_link))    
                reply = "New %s - %s" % (task.title, url)
                irc.send_to_channel(reply)
                
                log.debug('Adding %s to known ids' % bugid)
                lp_ids.append(bugid)

        first_run = False
        sleep(300)

@register_hook(name='ircbot_parsemsg_hook')
def lookup_bug_info_ircbot_parsemsg_hook(config, log, irc, poll_result):
    """
    Parse the result of irc.poll() and look for txt matching LaunchPad
    bug id's.  If found, print bug info to the channel.
    
    """
    
    (from_nick, from_chan, msg, dest) = poll_result
    lp = Launchpad.login_anonymously('ius-tools', 'production')
    
    # don't respond to ourself:
    if from_nick == irc.nick:
        return
        
    bug_ids = []
    res = re.findall('#[0-9]+', msg)
    for match in res:
        bug_ids.append(match.lstrip('#'))
    
    res = re.findall('https:\/\/bugs\.launchpad\.net\/ius\/\+bug\/[0-9]+', msg)
    for match in res:
        _id = re.sub('https:\/\/bugs\.launchpad\.net\/ius\/\+bug\/', '', match)
        if _id:
            bug_ids.append(_id)
    
    for _id in bug_ids:
        log.debug('looking up bug #%s' % _id)
        try:
            bug = lp.bugs[int(_id)]
        except KeyError, e:
            log.debug('LaunchPad bug %s does not exist' % _id)
            reply = "I tried to lookup LP#%s, but it doesn't exist." % _id
            irc.send_to_channel(reply)
            continue
        
        url = shorten_url(unicode(bug.web_link))
        reply = "LP#%s - %s - %s" % (_id, bug.title, url)
        irc.send_to_channel(reply)
    