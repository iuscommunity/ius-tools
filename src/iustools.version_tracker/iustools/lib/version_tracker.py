
import os
import re
import urllib2
from glob import glob
from configobj import ConfigObj
from urllib import urlencode
from smtplib import SMTP
from socket import error


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

    try:
        content = urllib2.urlopen(request).read()
    except urllib2.URLError:
        return False

    versions = re.compile(pkg_dict['regex']).findall(content)
    
    # simple sorted does not work with versions containing
    # more than one decimal
    #version = sorted(versions, reverse=True)[0]
    versions = natsorted(versions)
    versions.reverse()
    try:
        version = versions[0]
    except IndexError:
        return False
    else:
        return version

from launchpadlib.launchpad import Launchpad
import os, sys

def bug_titles():
    '''Get titles for all bugs in the IUS Projects Launchpad'''
    titles = []
    launchpad = Launchpad.login_anonymously(os.path.basename(sys.argv[0]), 'production')
    ius = launchpad.projects.search(text='ius')[0]
    tasks = ius.searchTasks()
    for task in tasks:
        titles.append(task.bug.title)
    return titles

def compare_titles(titles, name, version):
    '''Using the tiles from bug_title() we can compare our software name and version with
the Launchpad Bug titles, this way we can see if a Bug already exits'''
    for title in titles:
        mytitle = 'UPDATE REQUEST: ' +  name + ' ' +  str(version) + ' is available upstream'
        if title == mytitle:
            return True

def create_bug(name, version, url):
    '''Taking advantage of launchpadlib we can create a Launchpad Bug, 
it is assumed you first used compare_titles() to verify a bug does not already exits'''
    launchpad = Launchpad.login_with(os.path.basename(sys.argv[0]), 'production')
    ius = launchpad.projects.search(text='ius')[0]
    mytitle = 'UPDATE REQUEST: ' +  name + ' ' +  str(version) + ' is available upstream'
    launchpad.bugs.createBug(description='New Source from Upstream: ' + url, title=mytitle, target=ius)

def email(layout, layout_titles, output):
    '''Send email notifications using local SMTP server'''
    print '\nsending email...'
    fromaddr = 'IUS Coredev <ius-coredev@lists.launchpad.net>'
    toaddr = '<ius-coredev@lists.launchpad.net>'
    subject = '[ius-community] IUS Version Tracker'

    header = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n"
                    % (fromaddr, toaddr, subject))
    header = header + 'MIME-Version: 1.0\r\n'
    header = header + 'Content-Type: text/html\r\n\r\n'
 
    body = '<pre>'
    body = body + layout % layout_titles
    body = body + '\n'
    body = body + '='*75
    body = body + '\n'

    for p in output:
        body = body + layout % (p[0], p[1], p[2], p[3])
        body = body + '\n'

    body = body + '</pre>'
    msg = header + body

    try:
        server = SMTP('localhost')
        server.set_debuglevel(0)

    except error:
        print "Unable to connect to SMTP server"

    else:
        server.sendmail(fromaddr, toaddr, msg)
        server.quit()

