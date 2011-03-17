from glob import glob
from configobj import ConfigObj
import urllib2
from urllib import urlencode
from re import compile
from iustools.lib.natsort import natsorted
from cement.core.namespace import get_config

def packages():
    '''Return a list of all packages found in pkg_dir,
the configuration will contain needed regular expressions and 
URLs to grab latest software version number.'''
    config = get_config()
    pkg_dir = config['versiontracker']['pkg_dir']
    packages = []
    for _file in glob("%s/*.conf" % pkg_dir):
        c = ConfigObj(_file)
        if not c['enabled'] in [True, 'True', 'true', 1, '1']:
            continue
        packages.append(c)
    return packages

def package(pkg):
    '''Return a list of one package found in pkg_dir with given pkg name,
the configuration will contain needed regular expression and
URL to grab latest software version number.'''
    config = get_config()
    pkg_dir = config['versiontracker']['pkg_dir']
    package = []
    for _file in glob("%s/%s.conf" % (pkg_dir, pkg)):
        c = ConfigObj(_file)
        if not c['enabled'] in [True, 'True', 'true', 1, '1']:
            continue
        package.append(c)
    return package

def latest(p):
    '''Using our list from package() or packages() we extract data to make
the needed URL request, we then take the regex to pull the latest 
software version.'''
    request = urllib2.Request(p['url'])
    try:
        post = {p['post_value']: p['post_data']}
    except KeyError:
        pass
    else:
        request.add_data(urlencode(post))

    content = urllib2.urlopen(request).read()
    versions = compile(p['regex']).findall(content)
    # simple sorted does not work with versions containing
    # more than one decimal
    #version = sorted(versions, reverse=True)[0]
    versions = natsorted(versions)
    versions.reverse()
    version = versions[0]
    return version
