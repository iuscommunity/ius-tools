from re import compile
from urllib2 import urlopen, HTTPError
import sys

def get_link(package):
    '''get_link() retrieves the 'download file' link from the Launchpad files page'''
    url = 'http://bazaar.launchpad.net/~ius-coredev/ius/' + package + '/annotate/head%3A/SPECS/' + package +'.spec'
    request = urlopen(url)
    content = request.read()
    request.close()
    match = compile('<a href="(.*)">download file</a>').findall(content)
    match = 'http://bazaar.launchpad.net/' + match[0]
    return match

def get_download(link):
    '''get_download() returns the actual SPEC file from launchpad which can be printed'''
    request = urlopen(link)
    content = request.readlines()
    request.close()
    return content

def get_changelog(spec):
    '''get_changelog() uses the get_download() and parses for all content below %changelog'''
    
    linecount = 0
    changelog = False
    max_count = 0

    for line in spec:
        linecount += 1
        title = compile('%changelog').findall(line)

        # If we found %changelog using regex
        if title:
            changelog = linecount

        # If the changelog variable was set within title statement
        if changelog:

            # We only want to pull the last 5 changelog entries
            blank = compile('^$').findall(line)
            if blank:
                max_count += 1
                if max_count == 5:
                    sys.exit(0)

            print line,
