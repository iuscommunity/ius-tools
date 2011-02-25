"""
This is the RootController for the iustools application.  This can be used
to expose commands to the root namespace which will be accessible under:

    $ iustools --help
  
"""

import os, sys
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