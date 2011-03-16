"""getspec controller class to expose commands for iustools."""

from cement.core.controller import CementController, expose
from iustools.model.getspec import GetspecModel
from iustools.lib.lp import get_link, get_download, get_changelog
from urllib2 import HTTPError
import sys

class GetspecController(CementController):
          
    @expose()              
    def spec(self):
       
         # Check URL has data, if not Package does not exisit
        try:
            url = get_link(self.cli_args[1])
        except HTTPError as e:
            print e
            sys.exit(1)
        except IndexError:
            print 'Package Name must be given'
            sys.exit(1)

        # Load the entire file to the spec variable
        spec = get_download(url)

        # Print full SPEC
        for line in spec:
            print line,


    @expose()              
    def changelog(self):
       
         # Check URL has data, if not Package does not exisit
        try:
            url = get_link(self.cli_args[1])
        except HTTPError as e:
            print e
            sys.exit(1)
        except IndexError:
            print 'Package Name must be given'
            sys.exit(1)

        # Load the entire file to the spec variable
        spec = get_download(url)

        # Print only top 5 lines of changelog 
        get_changelog(spec)
