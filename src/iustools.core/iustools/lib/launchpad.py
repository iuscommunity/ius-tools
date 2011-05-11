
import re
import sys
from urllib2 import urlopen, HTTPError
from launchpadlib.launchpad import Launchpad

from cement.core.log import get_logger

from iustools.core.exc import IUSToolsRuntimeError, IUSToolsArgumentError
from iustools.lib.bitly import shorten_url

log = get_logger(__name__)

def get_link(package):
    """
    Retrieves the 'download file' link from LaunchPad files link.
    """
    base_url = 'http://bazaar.launchpad.net/~ius-coredev/ius/'
    url =  "%s/%s/annotate/head%%3A/SPECS/%s.spec" % (base_url, package, 
                                                     package)
    request = urlopen(url)
    content = request.read()
    request.close()
    match = re.compile('<a href="(.*)">download file</a>').findall(content)
    match = 'http://bazaar.launchpad.net/' + match[0]
    return match

def get_file(url):
    """
    Get the contents of a file downloaded from LaunchPad.
    """
    request = urlopen(url)
    return request

def get_spec(package):
    """
    Get the contents of an IUS package spec file.
    """
    try:
        url = get_link(package)
    except HTTPError, e:
        raise IUSToolsRuntimeError, e.args[0]

    spec = get_file(url).read()
    return spec
    
def get_changelog(package):
    """
    Get the RPM ChangeLog for an IUS Package.
    """
    
    changelog = False    
    out_txt = ''
    
    try:
        url = get_link(package)
    except HTTPError, e:
        raise IUSToolsRuntimeError, e.args[0]

    spec = get_file(url)
    
    for line in spec.readlines():
        if line.startswith('%changelog'):
            changelog = True

        if changelog:
            out_txt = out_txt + line    
    return out_txt

def get_bug(bug):
    """
    Get information for a bug.
    """
    lp = Launchpad.login_anonymously('ius-tools', 'production')
    bug_id = int(bug.lstrip('LP#').strip())
    log.debug('looking up bug #%s' % bug_id)
    try:
        bug = lp.bugs[int(bug_id)]
    except KeyError, e:
        raise IUSToolsArgumentError, \
            'LaunchPad bug %s does not exist' % bug_id
    
    url = shorten_url(unicode(bug.web_link))
    out_txt = "LP#%s - %s - %s" % (bug_id, bug.title, url)
    return out_txt

def get_package_repo(package):
    """
    Get a package's bzr repo URL.
    """
    lp = Launchpad.login_anonymously('ius-tools', 'production')
    ius = lp.projects.search(text='ius')[0]

    # Package Search
    pkg = lp.branches.getByUrl(url='lp:~ius-coredev/ius/%s' % package)

    if pkg:
        out_txt = '%s' % shorten_url(pkg.web_link)
    else:
        raise IUSToolsArgumentError, '%s does not exist' % package

    return out_txt