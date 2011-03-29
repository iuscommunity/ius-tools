from re import compile
from urllib2 import urlopen

def getrelease():
    req = urlopen('http://dl.iuscommunity.org/pub/ius/testing/Redhat/')
    content = req.read()
    release = compile('alt="\[DIR\]"></td><td><a href="([\d.]*)/">').findall(content)
    return release

def getpackage(release):
    req = urlopen('http://dl.iuscommunity.org/pub/ius/testing/Redhat/' + release + '/SRPMS/')
    content = req.read()
    packages = compile('<a href=".*src.rpm">(.*).src.rpm</a></td><td align="right">(.*)  </td><td align="right">').findall(content)
    return packages
