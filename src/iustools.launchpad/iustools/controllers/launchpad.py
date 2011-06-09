"""launchpad controller class to expose commands for iustools."""

from iustools.core.controller import IUSToolsController, expose
from iustools.lib import launchpad as ius_lp
from iustools.core.exc import IUSToolsArgumentError

class LaunchPadController(IUSToolsController):
    @expose(namespace='root', irc_command='.packagerepo')
    def package_repo(self):
        try:
            out_txt = ius_lp.get_package_repo(self.cli_args[1])
            print out_txt
            return dict(irc_data=out_txt)
        except IndexError, e:
            raise IUSToolsArgumentError, "Package name required."

    @expose(namespace='root', irc_command='.bug')
    def bug(self):
        """ 
        Look up bug info, expects next argument to be an ID.
        """
        try:
            out_txt = ius_lp.get_bug(self.cli_args[1])
            print out_txt
            return dict(irc_data=out_txt)
        except IndexError, e:
            raise IUSToolsArgumentError, "Bug number required."
        
    @expose(namespace='root')
    def spec(self):
        try:
            out_txt = ius_lp.get_spec(self.cli_args[1])
            print out_txt
            return dict(spec=out_txt)
        except IndexError, e:
            raise IUSToolsArgumentError, "Package name required."
        
    @expose(namespace='root')
    def changelog(self):
         # Check URL has data, if not Package does not exisit
        try:
            out_txt = ius_lp.get_changelog(self.cli_args[1])
            print out_txt
            return dict(changelog=out_txt)
        except IndexError, e:
            raise IUSToolsArgumentError, "Package name required."