"""Admin controller class to expose commands for iustools."""

import re
import os
import hashlib
import shutil
import sys
import pexpect
from datetime import datetime
from urllib import urlopen
from cement.core.log import get_logger
from cement.core.namespace import get_config

from iustools.core.controller import IUSToolsController, expose
from iustools.helpers.misc import exec_command, get_input
from iustools.helpers.smtp import send_mail
from iustools.core import exc

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
    def _get_tasks(self, tag_label, dest_path):
        tasks = []
        res = self._wrap(self.mf.tag.get_one, tag_label, 'ius')
               
        tag = res['data']['tag']
        for build_label in tag['builds']:
            log.debug("-> processing build %s" % build_label)
            res = self._wrap(self.mf.build.get_one, build_label, 'ius')
            for task_label in res['data']['build']['tasks']:
                log.debug("   -> processing task %s" % task_label)
                params = "task_label=%s&project_label=%s" % \
                         (task_label, 'ius')
                res = self._wrap(self.mf.request, 
                                 '/util/get_all_task_data?%s' % params)

                task = res['data']['task']
                for key in res['data'].keys():
                    task[key] = res['data'][key]
                
                task['repo_path'] = os.path.join(
                    dest_path,
                    tag_label,
                    task['target']['tag_path']
                    )
                tasks.append(task)
        return tasks
            
    @expose(namespace='admin')              
    def gen_repo(self):
        config = get_config()
        dest_base = os.path.join(config['admin']['repo_base_path'], 'ius')
        dest_base = os.path.abspath(dest_base)
        tmp_base = "%s.tmp" % dest_base
        
        if os.path.exists(tmp_base):
            shutil.rmtree(tmp_base)
            
        if self.cli_opts.sign and not self.cli_opts.gpg_passphrase:
            self.cli_opts.gpg_passphrase = get_input("GPG Key Passphrase: ",
                                                     suppress=True)
            
        repo_paths = []
        orig_dir = os.curdir
        orig_dir = os.curdir

        log.info('Local repo is %s' % dest_base)
        
        if self.cli_opts.clean:
            if os.path.exists(dest_base):
                log.info('Removing existing data')
                shutil.rmtree(dest_base)

        # first generate initial repos... cause, if say there are no
        # builds in 'testing' then the repos would get created and we always
        # want them there even if empty.
        for rel_label in config['admin']['managed_releases']:
            res = self._wrap(self.mf.release.get_one, rel_label)
            
            for target_label in res['data']['release']['targets']:
                res2 = self._wrap(self.mf.target.get_one, target_label)

                # first the source dirs
                for tag_label in config['admin']['managed_tags']:
                    dest = os.path.join(
                        tmp_base,
                        tag_label,
                        res2['data']['target']['distro_label'],
                        str(res2['data']['target']['full_version']),
                        'source',
                        )
                    dest = os.path.abspath(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                        
                arch_label = res2['data']['target']['arch_label']
                if arch_label not in config['admin']['managed_archs']:
                    continue
                    
                for tag_label in config['admin']['managed_tags']:
                    dest = os.path.abspath(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                        
                    dest = os.path.join(
                        tmp_base,
                        tag_label,
                        res2['data']['target']['tag_path']
                        )
                    dest = os.path.abspath(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    
                    # and the debuginfo dirs
                    dest = os.path.join(
                        tmp_base,
                        tag_label,
                        res2['data']['target']['tag_path'],
                        'debuginfo',
                        )
                    dest = os.path.abspath(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                        
                    

        for tag_label in config['admin']['managed_tags']:
            log.info("Pulling files for tag %s" % tag_label)
            tasks = self._get_tasks(tag_label, tmp_base)
            
            for task in tasks:
                if task['repo_path'] not in repo_paths:
                    repo_paths.append(task['repo_path'])

                debuginfo_path = os.path.join(task['repo_path'], 'debuginfo')
                if debuginfo_path not in repo_paths:
                    repo_paths.append(debuginfo_path)
                    
                if not os.path.exists(task['repo_path']):
                    os.makedirs(task['repo_path'])
                if not os.path.exists(debuginfo_path):
                    os.makedirs(debuginfo_path)
                    
                for _file in task['files']:
                    if re.search("debuginfo", _file):
                        os.chdir(debuginfo_path)
                        prev_dest = os.path.join(
                                        dest_base,
                                        tag_label,
                                        task['target']['tag_path'],
                                        'debuginfo',
                                        _file
                                        )
                    else:
                        os.chdir(task['repo_path'])
                        prev_dest = os.path.join(
                                        dest_base,
                                        tag_label,
                                        task['target']['tag_path'],
                                        _file
                                        )
                    file_path = '%s/files/%s' % (task['fs_path'], _file)
                    
                    
                    
                    # Create a hardlink if it existes prevously
                    if os.path.exists(prev_dest):
                        log.debug("Hard linking from: %s" % prev_dest)
                        os.link(prev_dest, _file)
                        continue

                    res = self._wrap(self.mf.root.get_file_download_url, 
                                     file_path)
                    f_url = res['data']['download_url']
                    log.debug('Downloading: %s' % f_url)
                    f_contents = urlopen(f_url).read()
                    f = open(_file, 'w+')
                    f.write(f_contents)
                    f.close()
                os.chdir(orig_dir)
        
                if task['target']['arch_label'] == 'i386':
                    src_repo_path =  os.path.join(
                        os.path.dirname(task['repo_path']), 'source'
                        )

                    if not os.path.exists(src_repo_path):
                        os.makedirs(src_repo_path)
                    if src_repo_path not in repo_paths:
                        repo_paths.append(src_repo_path)

                    os.chdir(src_repo_path)
                    for _file in task['sources']:
                        file_path = '%s/sources/%s' % (task['fs_path'], _file)                        
                        prev_dest = os.path.join(
                                    dest_base,
                                    tag_label,
                                    task['target']['distro_label'],
                                    str(task['target']['full_version']),
                                    'source',
                                    _file
                                    )

                        # Create a hardlink if it existes prevously
                        if os.path.exists(prev_dest):
                            log.debug("Hard linking from: %s" % prev_dest)
                            os.link(prev_dest, _file)
                            continue
                        
                        res = self._wrap(self.mf.root.get_file_download_url, 
                                         file_path)
                        f_url = res['data']['download_url']
                        log.debug('Downloading %s' % f_url)
                        f_contents = urlopen(f_url).read()
                        f = open(_file, 'w+')
                        f.write(f_contents)
                        f.close()
                    os.chdir(orig_dir)

        repo_paths.sort()
        
        # sign files
        if self.cli_opts.sign:
            self.sign_packages(self.cli_opts.gpg_passphrase, repo_paths)
            
        # createrepos
        self.create_repo_metadata(repo_paths)

        # create current hash
        _hash = hashlib.md5(datetime.now().__str__()).hexdigest()
        current = os.path.join(tmp_base, 'CURRENT')
        log.info("Updating CURRENT file with hash: %s" % _hash)
        f = open(current, 'w+')
        f.write(_hash)
        f.close()

        if os.path.exists(dest_base):
            shutil.rmtree(dest_base)
        log.debug("Moving %s -> %s" % (tmp_base, dest_base))
        shutil.move(tmp_base, dest_base)
        
        return dict()

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
            
    def create_repo_metadata(self, path_list=[]):
        """
        Generate Yum metadata in each director of path_list.
        
        Required Arguments:
        
            path_list
                The list of directories to run createrepo on.
                
        """
        log.info("Generating repository metadata")
        config = get_config()
        start = len(config['admin']['repo_base_path'].split('/'))
        for path in path_list:
            log.info("  `-> %s" % '/'.join(path.split('/')[start:]))
            os.system('createrepo -s md5 %s >/dev/null' % path)
            
    def sign_packages(self, passphrase, path_list=[]):
        """
        Sign all files matching *.rpm in path_list.
        
        Required Arguments:
        
            passphrase
                The GPG key passphrase.
                
            path_list
                The list of directories to sign *.rpm in.
                
        """
        config = get_config()
        paths = '/*.rpm '.join(path_list)
        cmd = "%s --resign %s/*.rpm >/dev/null" % \
              (config['rpm_binpath'], paths)
        try:
            child = pexpect.spawn(cmd)
            child.expect('Enter pass phrase:')
            child.send(passphrase)
        except pexpect.EOF, e:
            pass
            
    @expose(namespace='admin')
    def push_to_public(self):
        config = get_config()
        log.info("pushing changes to %s" % config['admin']['remote_rsync_path'])
        if self.cli_opts.delete:
            os.system('%s -az --delete %s/ %s/ >/dev/null' % \
                     (config['admin']['rsync_binpath'],
                      config['admin']['repo_base_path'],
                      config['admin']['remote_rsync_path']))
        else:
            os.system('%s -az %s/ %s/ >/dev/null' % \
                     (config['admin']['rsync_binpath'],
                      config['admin']['repo_base_path'],
                      config['admin']['remote_rsync_path']))

    @expose(namespace='admin')
    def sync(self):
        # prompt now so it doesn't later
        if self.cli_opts.sign and not self.cli_opts.gpg_passphrase:
            self.cli_opts.gpg_passphrase = get_input("GPG Key Passphrase: ",
                                                     suppress=True)
        self.process_tags()
        self.gen_repo()
        #self.push_to_public()

