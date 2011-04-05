"""version_tracker controller class to expose commands for iustools."""

from cement.core.controller import CementController, expose
from cement.core.namespace import get_config

from iustools.core.exc import IUSToolsArgumentError
from iustools.helpers.compare import vcompare
from iustools.lib.version_tracker import get_upstream_version, get_ius_version
from iustools.lib.version_tracker import get_packages


class colors:
    red = '\033[91m'
    green = '\033[92m'
    blue = '\033[94m'
    yellow = '\033[33m'
    end = '\033[0m'

config = get_config()

TAGS = ['testing', 'stable']
RELEASES = ['4', '5']

class VersionTrackerController(CementController):

    @expose(namespace='version_tracker')
    def default(self):
        """
        List the version tracker report.
        """
        packages = get_packages(name=self.cli_opts.package,
                                filter_name=self.cli_opts.filter)
        
        if not self.cli_opts.release:
            raise IUSToolsArgumentError, "A valid --release is required."
        elif self.cli_opts.release not in RELEASES:
            raise IUSToolsArgumentError, "Invalid release."
            
        if packages:
            # Print out our Packages and Info
            print
            print config['version_tracker']['layout'] % \
                config['version_tracker']['layout_titles']
            print '='*75

            for pkg_dict in sorted(packages, key=lambda a: a['name']):
                upstream_ver = get_upstream_version(pkg_dict)
                ius_ver = get_ius_version(pkg_dict['name'], 
                                          self.cli_opts.release, 
                                          'stable')

                # verify we pulled a version
                if upstream_ver:
                
                    # package didn't exist
                    if not ius_ver:
                        continue
                        
                    if ius_ver == upstream_ver:
                        status = 'current'
                        color = colors.green
                        
                    else:
                        status = 'outdated'
                        color = colors.red
                        
                        # Since its out of date we should check testing
                        ius_test = get_ius_version(pkg_dict['name'], 
                                                   self.cli_opts.release, 
                                                   'testing')
                        if ius_test:
                            if ius_test == upstream_ver:
                                ius_ver = ius_test
                                status = 'testing'
                                color = colors.yellow
                            else:
                                ius_ver = ius_test
                                status = 'testing outdated'
                                color = colors.red

                else:
                    status = 'unknown'
                    color = colors.red
                    upstream_ver = '??????'

                # Print out for the viewer
                print config['version_tracker']['layout'] % \
                        (pkg_dict['name'], ius_ver, upstream_ver, 
                         color + status + colors.end)

            print
            return dict(packages=packages)
                
        else:
            print "No data found using pkg dir '%s'" % \
                    config['version_tracker']['pkg_dir']
            return dict(packages=[])
