"""
This is the RootController for the iustools application.  This can be used
to expose commands to the root namespace which will be accessible under:

    $ iustools --help
  
"""

import re
import os
import sys
import json
from urllib2 import urlopen, HTTPError
from datetime import datetime, timedelta
from operator import itemgetter

from cement.core.namespace import get_config
from cement.core.log import get_logger

from iustools.core.exc import IUSToolsArgumentError
from iustools.core.controller import IUSToolsController, expose
from iustools.lib.testing_age import getrelease, getpackage
from iustools.lib.bitly import shorten_url

log = get_logger(__name__)
config = get_config()

class RootController(IUSToolsController):
    @expose('mf.templates.root.api_error', is_hidden=True)
    def api_error(self, errors=[]):
        """
        This method is intended specifically for displaying the errors dict
        as returned by MF Hub.

        Required Arguments:

            errors
                A dictionary in the form of {'ErrorCode': 'Error message'}.


        The best way to use this is with the '_abort_on_api_error' function of
        MFController.

        .. code-block:: python

            from mf.core.controller import MFController

            class DistroController(MFController):
                @expose(namespace='distro')
                def create(self, *args, **kw):
                    res = self.hub.distro.create(dict(label='test', display_name='Test Distro'))
                    self._abort_on_api_error(res['errors'])

                    # continue work (no errors)

        """
        if config.has_key('nosetests') and config['nosetests']:
            print errors
        return dict(errors=errors)
        
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

    @expose()
    def testing_age(self):
        # Get our dictionary
        rpms = {}
        res_dict = {}
        res_dict['packages'] = []
        
        # Define our Month dictionary
        months = {}
        months['Jan'] = 1
        months['Fed'] = 2
        months['Mar'] = 3
        months['Apr'] = 4
        months['May'] = 5
        months['Jun'] = 6
        months['Jul'] = 7
        months['Aug'] = 8
        months['Sep'] = 9
        months['Oct'] = 10
        months['Nov'] = 11
        months['Dec'] = 12
        
        for release in getrelease():
            packages = getpackage(release)
            for package in packages:
                # the date format for right now
                now = datetime.now().date()
                timestamp = package[1].split('-')
                day = timestamp[0]
                month = timestamp[1]
                month = months[month]
                year = timestamp[2].split()
                year = year[0]

                date = datetime(int(year), int(month), int(day)).date()
                delta = (now - date)
                rpms[package[0]] = int(delta.days)

        print '%-10s %s' % ('Age', 'Package')
        print '-'*45
        for package in sorted(rpms):
            print '%-10s %s' % (rpms[package], package)
            res_dict['packages'].append( (rpms[package], package) )

        return res_dict
