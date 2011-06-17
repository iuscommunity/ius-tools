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
from iustools.helpers.misc import exec_command
from iustools.core import exc

log = get_logger(__name__)
config = get_config()

class AdminController(IUSToolsController):
    @expose(namespace='admin')
    def test(self):
        #print self._wrap(self.mf.tag.get_one, 'testing', 'ius')
        res = self._get_tasks('stable')
        for task in res:
            print task['repo_path']
        
    def _get_tasks(self, tag_label):
        tasks = []
        dest_base = os.path.join(config['admin']['repo_base_path'], 'ius')
        dest_base = os.path.abspath(dest_base)
        
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
                    dest_base,
                    tag_label,
                    task['target']['tag_path']
                    )
                tasks.append(task)
        return tasks
                
    @expose(namespace='admin')              
    def gen_repo(self):
        if self.cli_opts.sign and not self.cli_opts.gpg_passphrase:
            try:
                os.system('stty -echo')
                res = raw_input('GPG Key Passphrase: ')
            except Exception:
                print
                sys.exit(1)
            finally:
                print
                os.system('stty echo')
                
            self.cli_opts.gpg_passphrase = res.strip('\n')
            
        repo_paths = []
        orig_dir = os.curdir
        orig_dir = os.curdir
         
        if self.cli_opts.tag_label:
            config['admin']['managed_tags'] = self.cli_opts.tag_label\
                                              .split(',')
            
        dest_base = os.path.join(config['admin']['repo_base_path'], 'ius')
        dest_base = os.path.abspath(dest_base)

        log.info('Destination: %s' % dest_base)
        
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
                        dest_base,
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
                        dest_base,
                        tag_label,
                        res2['data']['target']['tag_path']
                        )
                    dest = os.path.abspath(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    

        for tag_label in config['admin']['managed_tags']:
            log.info("Pulling files for tag %s" % tag_label)
            tasks = self._get_tasks(tag_label)
            
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
                    else:
                        os.chdir(task['repo_path'])
                        
                    file_path = '%s/files/%s' % (task['fs_path'], _file)

                    # only download if its missing
                    if os.path.exists(_file):
                        continue

                    res = self._wrap(self.mf.root.get_file_download_url, 
                                     file_path)
                    f_url = res['data']['download_url']
                    log.debug('attempting to download %s' % f_url)
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
                        
                        # only download if its missing
                        if os.path.exists(_file):
                            continue
                        
                        res = self._wrap(self.mf.root.get_file_download_url, 
                                         file_path)
                        f_url = res['data']['download_url']
                        log.debug('attempting to download %s' % f_url)
                        f_contents = urlopen(f_url).read()
                        f = open(_file, 'w+')
                        f.write(f_contents)
                        f.close()
                    os.chdir(orig_dir)

        repo_paths.sort()
        
        # sign files
        if self.cli_opts.sign:
            paths = '/*.rpm '.join(repo_paths)
            cmd = "%s --resign %s/*.rpm >/dev/null" % \
                  (config['rpm_binpath'], paths)
            try:
                child = pexpect.spawn(cmd)
                child.expect('Enter pass phrase:')
                child.send(self.cli_opts.gpg_passphrase)
            except pexpect.EOF, e:
                pass
            
        # createrepos
        log.info("Generating repository metadata")
        for path in repo_paths:
            _path = re.sub(dest_base, '', path)
            log.info("  `-> %s" % _path)
            os.system('createrepo -s md5 %s >/dev/null' % path)

        # create current hash
        current = os.path.join(dest_base, 'CURRENT')
        log.info("Updating: %s" % current)
        f = open(current, 'w+')
        f.write(hashlib.md5(datetime.now().__str__()).hexdigest())
        f.close()

        return dict()


    @expose(namespace='admin')
    def push_to_public(self):
        log.info("pushing changes to %s" % config['ius']['remote_rsync_path'])
        if self.cli_opts.delete:
            os.system('rsync -az --delete %s/ %s/' % (config['ius']['repo_base_path'],
                                                   config['ius']['remote_rsync_path']))
        else:
            os.system('rsync -az %s/ %s/' % (config['ius']['repo_base_path'],
                                                   config['ius']['remote_rsync_path']))

    @expose(namespace='admin')
    def sync(self):
        self.gen_repo()
        self.push_to_public()

