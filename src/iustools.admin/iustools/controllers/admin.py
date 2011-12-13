"""Admin controller class to expose commands for iustools."""

import re
import os
import hashlib
import shutil
import sys
import pexpect
from glob import glob
from datetime import datetime
from urllib import urlopen
from cement.core.log import get_logger
from cement.core.namespace import get_config

from iustools.core.controller import IUSToolsController, expose
from iustools.helpers.misc import exec_command, get_input
from iustools.helpers.smtp import send_mail
from iustools.core import exc
from iustools.lib.repo import IUSRepo

log = get_logger(__name__)

FOOTER = """

Please note that downstream mirrors take anywhere from 1-24 hours to sync.


======================================================================
Installing From IUS Repositories
----------------------------------------------------------------------

First read the Getting Started guide here:

	http://iuscommunity.org/Docs/GettingStarted/


Then either install:

    root@linuxbox ~]# yum install <package1> <package2>


OR upgrade if you already have IUS Packages installed:

    root@linuxbox ~]# yum upgrade


Additionally, if you'd like to install or upgrade a package from 'testing' 
simply do the following:

    root@linuxbox ~]# yum install <package1> --enablerepo=ius-testing
    
    root@linuxbox ~]# yum upgrade <package1> --enablerepo=ius-testing



======================================================================
Reporting Bugs
----------------------------------------------------------------------

Any and all feedback is greatly appreciated.  Please report all bugs to:

	http://bugs.launchpad.net/ius


Thanks!


---
You received this message because you are subscribed to the 'ius-community' 
team list at http://launchpad.net/~ius-community

SITE: http://iuscommunity.org
BUGS: http://launchpad.net/ius
REPO: http://dl.iuscommunity.org
IRC: #iuscommunity

"""

TAG_MSG = """

The following builds have been tagged as '%s':
    
   - %s

%s

"""

TAG_AND_UNTAG_MSG = """

The following builds have been tagged as '%s':

   - %s


Additionally, the following older builds were moved to tag 'archive':

   - %s

%s

"""


class AdminController(IUSToolsController):
    @expose(namespace='admin')
    def gen_repo(self):
        config = get_config()
        if self.cli_opts.sign:
            passphrase = self.cli_opts.gpg_passphrase
            if not passphrase:
                passphrase = get_input("GPG Key Passphrase: ", suppress=True)
                
            repo = IUSRepo(config, self.mf, sign=True, 
                           gpg_passphrase=passphrase)
        else:
            repo = IUSRepo(config, self.mf)
            
        if self.cli_opts.clean:
            repo.clean()
            
        repo.get_files()
        repo.build_metadata()

    @expose(namespace='admin')
    def push_to_public(self):
        config = get_config()
        log.info("pushing changes to %s" % config['admin']['remote_rsync_path'])
        if self.cli_opts.delete:
            os.system('%s -az --delete %s/ius/ %s/ius/ --exclude %s >/dev/null' % \
                     (config['admin']['rsync_binpath'],
                      config['admin']['repo_base_path'],
                      config['admin']['remote_rsync_path'],
                      config['admin']['remote_exclude']))
        else:
            os.system('%s -az %s/ius/ %s/ius/ --exclude %s >/dev/null' % \
                     (config['admin']['rsync_binpath'],
                      config['admin']['repo_base_path'],
                      config['admin']['remote_rsync_path'],
                      config['admin']['remote_exclude']))

        # Internal IUS Push
        if config['admin']['internal_remote_rsync_path']:

            # remove any excludes if configured
            if config['admin']['internal_remote_exclude']:
                internal_remote_exclude = config['admin']['internal_remote_exclude']
                for exclude in internal_remote_exclude:
                    log.info("removing %s from %s" % (exclude, config['admin']['repo_base_path']))
                    for dirs in os.walk('%s/ius/' % config['admin']['repo_base_path']):
                        if exclude in ', '.join(dirs[2]):
                        path = dirs[0]
                        for f in dirs[2]:
                            if exclude in f:
                                os.remove('%s/%s' % (path, f))

                # rebuild our meta data now that
                # files have been removed
                repo.build_metadata()

            log.info("pushing changes to %s" % config['admin']['internal_remote_rsync_path'])
            if self.cli_opts.delete:
                os.system('%s -az --delete %s/ius/ %s/ >/dev/null' % \
                         (config['admin']['rsync_binpath'],
                          config['admin']['repo_base_path'],
                          config['admin']['internal_remote_rsync_path']))
            else:
                os.system('%s -az %s/ius/ %s/ >/dev/null' % \
                         (config['admin']['rsync_binpath'],
                          config['admin']['repo_base_path'],
                          config['admin']['internal_remote_rsync_path']))


    @expose(namespace='admin')
    def sync(self):
        # prompt now so it doesn't later
        if self.cli_opts.sign and not self.cli_opts.gpg_passphrase:
            self.cli_opts.gpg_passphrase = get_input("GPG Key Passphrase: ",
                                                     suppress=True)
        self.process_tags()
        self.gen_repo()
        self.push_to_public()

    def process_tag(self, tag_label):
        config = get_config()
        log.info("Processing tag %s" % tag_label)
        res = self._wrap(self.mf.tag.get_one, 
                         "%s-candidate" % tag_label, 
                         'ius')
        from_tag = res['data']['tag']
        
        res = self._wrap(self.mf.tag.get_one, tag_label, 'ius')
        to_tag = res['data']['tag']
        
        old_tag = None
        if tag_label == 'stable':
            res = self._wrap(self.mf.tag.get_one, 'archive', 'ius')
            old_tag = res['data']['tag']
        
        res = self._wrap(self.mf.tag.move_builds, 
                         from_tag['label'], 
                         'ius', 
                         to_tag['label']) 
        untagged_builds = res['data']['untagged_builds']
        moved_builds = res['data']['moved_builds']
        
        if not len(moved_builds) > 0:
            return 
           
        # if tagging to stable, remove all other tags
        if to_tag['label'] == 'stable':
            res = self._wrap(self.mf.tag.get_all, dict(project_label='ius'))
            all_tags = res['data']['tags']
            for build in moved_builds:
                for _tag in all_tags:
                    if _tag['label'] == 'stable':
                        continue
                    res = self._wrap(self.mf.build.untag, 
                                     build, 
                                     'ius',
                                     _tag['label'])

        # if there were older untagged_builds move them to old_tag
        if old_tag and len(untagged_builds) > 0:
            msg = TAG_AND_UNTAG_MSG % (
                    to_tag['label'], 
                    "\n\r    - ".join(moved_builds),
                    "\n\r    - ".join(untagged_builds),
                    FOOTER
                    )
            for old_label in untagged_builds:
                res = self._wrap(self.mf.build.tag,
                                 old_label,
                                 'ius',
                                 old_tag['label'])
        else:
            msg = TAG_MSG % (
                    to_tag['label'], 
                    "\n\r   - ".join(moved_builds),
                    FOOTER
                    )
        
        for build in moved_builds:
            log.info("  `-> %s" % build)
           
        send_mail(config['admin']['announce_email'],
                  "new builds moved to tag '%s'" % to_tag['label'],
                  msg)
            
    @expose(namespace='admin')
    def process_tags(self):
        config = get_config()
        for tag_label in config['admin']['managed_tags']:
            self.process_tag(tag_label)
