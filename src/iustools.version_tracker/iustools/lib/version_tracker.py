
import os
import re
import urllib2
from glob import glob
from configobj import ConfigObj
from urllib import urlencode

from cement.core.namespace import get_config

from iustools.helpers.natsort import natsorted

config = get_config()

def get_ius_version(name, release, tag):
    request = urllib2.urlopen('%s/%s/Redhat/%s/SRPMS/' % \
                             (config['version_tracker']['ius_baseurl'], 
                              tag, 
                              release))
    content = request.read()
    match = re.compile(name + '-([0-9.]*)-.*.src.rpm').findall(content)
    try:
        ius_ver = sorted(match, reverse=True)[0]
    except IndexError, e:
        # package doesn't exist in this release
        ius_ver = None
    return ius_ver
    
def get_packages(name=None, only_enabled=True, filter_name=None):
    """
    Return a list of all packages found in pkg_dir, the configuration will 
    contain needed regular expressions and URLs to grab latest software 
    version number.
    
    Optional Parameters:
        
        only_enabled
            Only return a list of packages that are currently enabled.
            
        filter_name
            If filter_name is passed, only return packages that match the 
            filter string.  I.e. A filter of 'php' would match 'php52', 
            'php53', etc.
            
    Returns: list
    
    """
    
    pkg_dir = config['version_tracker']['pkg_dir']
    packages = []
    
    if name:
        glob_path = "%s/%s.conf" % (pkg_dir, name)
    else:
        glob_path = "%s/*.conf" % pkg_dir
        
    for _file in glob(glob_path):
        # if filter_name is passed, only include if the file matches
        if filter_name:
            if not re.search(filter_name, os.path.basename(_file)):
                continue
                
        c = ConfigObj(_file)
        if only_enabled:
            if not c['enabled'] in [True, 'True', 'true', 1, '1']:
                continue
        packages.append(c)
    return packages

def get_upstream_version(pkg_dict):
    """
    Using our list from get_packages() we extract data to make the 
    needed URL request, we then take the regex to pull the latest software 
    version.
    
    Required Arguments:
    
        pkg_dict
            The package dictionary, as returned by get_package() or 
            get_packages().
            
    """
    
    request = urllib2.Request(pkg_dict['url'])
    try:
        post_vars = {pkg_dict['post_value']: pkg_dict['post_data']}
    except KeyError:
        pass
    else:
        request.add_data(urlencode(post_vars))

    content = urllib2.urlopen(request).read()
    versions = re.compile(pkg_dict['regex']).findall(content)
    
    # simple sorted does not work with versions containing
    # more than one decimal
    #version = sorted(versions, reverse=True)[0]
    versions = natsorted(versions)
    versions.reverse()
    version = versions[0]
    return version