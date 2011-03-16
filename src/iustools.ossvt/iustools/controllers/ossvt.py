"""ossvt controller class to expose commands for iustools."""

from cement.core.controller import CementController, expose
from iustools.model.ossvt import OssvtModel
from cement.core.namespace import get_config
from iustools.lib.upstream import package, packages, latest 
from iustools.lib.ius import ius_version
from iustools.lib.ver_compare import vcompare
import argparse

class colors:
    pink = '\033[95m'
    red = '\033[91m'
    green = '\033[92m'
    gold = '\033[93m'
    blue = '\033[94m'
    end = '\033[0m'

config = get_config()

class OssvtController(CementController):

    @expose(namespace='ossvt')
    def versions(self):

        if config['ossvt']['name']:
            pkg = package(config['ossvt']['name'])
            with_launchpad = False
        else:
            pkg = packages()

        if pkg:
            # Print out our Packages and Info
            print '%-30s %-15s %-15s %s' % ('name', 'ius ver', 'upstream ver', 'status')
            print '='*75 

            for p in pkg:
                upstream_ver = latest(p)
                ius_ver = ius_version(p['name'])

                compare = vcompare(ius_ver, upstream_ver)
                
                # Print if package is out of date
                if compare:
                    print '%-30s %-15s %-15s %s' % (
                                                    p['name'], 
                                                    ius_ver, 
                                                    upstream_ver, 
                                                    colors.red + 'outdated' + colors.end
                                                   )

                # Print if package is up to date
                else:
                    if config['ossvt']['with_up2date']:
                        print '%-30s %-15s %-15s %s' % (
                                                        p['name'], 
                                                        ius_ver, 
                                                        upstream_ver, 
                                                        colors.green + 'updated' + colors.end
                                                       )
