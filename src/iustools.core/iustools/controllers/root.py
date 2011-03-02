"""
This is the RootController for the iustools application.  This can be used
to expose commands to the root namespace which will be accessible under:

    $ iustools --help
  
"""

import re
import os
import sys
import json
from urllib2 import urlopen
from launchpadlib.launchpad import Launchpad

from cement.core.controller import CementController
from cement.core.namespace import get_config
from cement.core.log import get_logger

from iustools.core.exc import IUSToolsArgumentError
from iustools.core.controller import expose

log = get_logger(__name__)
config = get_config()

class RootController(CementController):
    @expose('iustools.templates.root.error', is_hidden=True)
    def error(self, errors=[]):
        """
        This can be called when catching exceptions giving the developer a 
        clean way of presenting errors to the user.
        
        Required Arguments:
        
            errors
                A list of tuples in the form of [('ErrorCode', 'Error message')].
        
        
        The best way to use this is with an 'abort' function... something like:
        
        .. code-block:: python
        
            from cement.core.controller import run_controller_command
            
            def abort(errors):
                run_controller_command('root', 'error', errors=errors)
            
            errors = []
            # do something, if error
            errors.append(('MyErrorCode', 'My Error Message'))
            
            abort(errors)
            
            # continue work (no errors)
            
        """
        return dict(errors=errors)
    
    @expose(is_hidden=True)
    def nosetests(self):
        """This method is added for nose testing."""
        pass
        
    @expose(is_hidden=True)
    def default(self):
        """
        This is the default command method.  If no commands are passed to
        iustools, this one will be executed.  By default it raises an
        exception.
        
        """
        raise IUSToolsArgumentError, "A command is required. See --help?"
    
    @expose(irc_command='.packagerepo')
    def get_package_repo(self):
        try:
            package = self.cli_args[1]
        except IndexError, e:
            raise IUSToolsArgumentError, "expecting a second argument (package name)."
            
        lp = Launchpad.login_anonymously('ius-tools', 'production')
        ius = lp.projects.search(text='ius')[0]

        # Package Search
        lp_pkg = lp.branches.getByUrl(url='lp:~ius-coredev/ius/%s' % package)

        if lp_pkg:
            out_txt = '%s' % lp_pkg.web_link
        else:
            raise IUSToolsArgumentError, '%s does not exist' % package

        print out_txt
        return dict(irc_data=out_txt)

    @expose(irc_command='.bug')
    def bug_info(self):
        """ 
        Look up bug info, expects next argument to be an ID.
        """
        lp = Launchpad.login_anonymously('ius-tools', 'production')
    
        try:
            bug_id = int(self.cli_args[1].lstrip('LP#').strip())
        except ValueError, e:
            raise IUSToolsArgumentError, e.args[0]
            
        log.debug('looking up bug #%s' % bug_id)
        try:
            bug = lp.bugs[int(bug_id)]
        except KeyError, e:
            raise IUSToolsArgumentError, \
                'LaunchPad bug %s does not exist' % bug_id
        
        bitly_url = "%s?format=json&longUrl=%s&login=%s&apiKey=%s" % (
                    config['ircbot']['bitly_baseurl'],
                    unicode(bug.web_link),
                    config['ircbot']['bitly_user'],
                    config['ircbot']['bitly_apikey'],
                    )
        bitly_url = re.sub('\+', '%2b', bitly_url)
    
        res = urlopen(bitly_url)
        data = json.loads(res.read())
        short_url = data['data']['url']
    
        out_txt = "LP#%s - %s - %s" % (bug_id, bug.title, short_url)
        print out_txt
        return dict(irc_data=out_txt)
        