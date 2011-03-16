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
