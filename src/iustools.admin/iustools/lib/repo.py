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

log = get_logger(__name__)

class IUSRepo(object):
    def __init__(self, config, mf_hub, sign=False, gpg_passphrase=None):
        self.config = config
        self.mf = mf_hub
        self.sign_packages = sign
        self.gpg_passphrase = gpg_passphrase
        self.local_path = os.path.join(self.config['admin']['repo_base_path'], 'ius')
        self.tmp_path = "%s.tmp" % self.local_path
        self.gpg_key_path = self.config['admin']['gpg_key_file_path']
        self.eua_path = self.config['admin']['eua_file_path']
        
        if os.path.exists(self.tmp_path):
            shutil.rmtree(self.tmp_path)
        os.makedirs(self.tmp_path)

    def fix_path(self, path):
        path = os.path.abspath(path)
        path = re.sub('redhat', 'Redhat', path)
        return path
        
    def get_repo_paths(self, base_path):
        repo_paths = []
        for rel_label in self.config['admin']['managed_releases']:
            res = self._wrap(self.mf.release.get_one, rel_label)
            
            for target_label in res['data']['release']['targets']:
                res2 = self._wrap(self.mf.target.get_one, target_label)

                # first the source dirs
                for tag_label in self.config['admin']['managed_tags']:
                    dest = os.path.join(
                        base_path,
                        tag_label,
                        res2['data']['target']['distro_label'],
                        str(res2['data']['target']['full_version']),
                        'SRPMS',
                        )
                    dest = self.fix_path(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)
                        
                arch_label = res2['data']['target']['arch_label']
                if arch_label not in self.config['admin']['managed_archs']:
                    continue
                    
                for tag_label in self.config['admin']['managed_tags']:
                    dest = os.path.join(
                        base_path,
                        tag_label,
                        res2['data']['target']['tag_path']
                        )
                    dest = self.fix_path(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)

                    # and the debuginfo dirs
                    dest = os.path.join(
                        base_path,
                        tag_label,
                        res2['data']['target']['tag_path'],
                        'debuginfo',
                        )
                    dest = self.fix_path(dest)
                    if dest not in repo_paths:
                        repo_paths.append(dest)

        repo_paths.sort()
        return repo_paths
        
    def _wrap(self, func, *args, **kw):
        try:
            res = func(*args, **kw)
            self._abort_on_api_error(res['errors'])
            return res
        except HTTPError, e:
            raise exc.IUSToolsRuntimeError, \
                "An HTTPError was received: '%s %s'." % \
                (e.code, e.msg)

    def _abort_on_api_error(self, errors={}):
        if len(errors) > 0:
            if self.config['output_handler'] == 'json':
                run_controller_command('root', 'api_error_json', errors=errors)
            else:
                run_controller_command('root', 'api_error', errors=errors)
            sys.exit(1)
            
    def get_tasks(self, tag_label):
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
                
                path = os.path.join(tag_label, task['target']['tag_path'])
                dest_path = self.fix_path(os.path.join(self.local_path, path))
                tmp_path = self.fix_path(os.path.join(self.tmp_path, path))
                
                task['dest_path'] = dest_path
                task['tmp_path'] = tmp_path
                task['debuginfo_path'] = os.path.join(dest_path, 'debuginfo')
                task['tmp_debuginfo_path'] = os.path.join(tmp_path, 'debuginfo')
                task['srpm_path'] = os.path.join(os.path.dirname(dest_path), 'SRPMS')
                task['tmp_srpm_path'] = os.path.join(os.path.dirname(tmp_path), 'SRPMS')
                tasks.append(task)
        return tasks
            
    def clean(self):
        log.info("Cleaning %s" % self.local_path)
        if os.path.exists(self.local_path):
            shutil.rmtree(self.local_path)
     
    def get_file(self, file_path, dest_path):
        res = self._wrap(self.mf.root.get_file_download_url, 
                         file_path)
        f_url = res['data']['download_url']
        log.debug('Downloading: %s' % f_url)
        f_contents = urlopen(f_url).read()
        f = open(dest_path, 'w+')
        f.write(f_contents)
        f.close()
        
        if self.sign_packages:
            self.sign_package(dest_path)
                        
    def get_files(self):
        repo_paths = self.get_repo_paths(self.tmp_path)
        for path in repo_paths:
            if not os.path.exists(path):
                os.makedirs(path)
                        
        for tag_label in self.config['admin']['managed_tags']:
            log.info("Pulling files for tag %s" % tag_label)
            tasks = self.get_tasks(tag_label)
            
            for task in tasks:
                for _file in task['files']:
                    if re.search("debuginfo", _file):
                        dest_path = os.path.join(task['debuginfo_path'], _file)
                        tmp_path = os.path.join(task['tmp_debuginfo_path'], _file)
                    else:
                        dest_path = os.path.join(task['dest_path'], _file)
                        tmp_path = os.path.join(task['tmp_path'], _file)
                    file_path = '%s/files/%s' % (task['fs_path'], _file)
                                        
                    # Create a hardlink if it existes prevously
                    if os.path.exists(dest_path):
                        log.debug("Hard linking from: %s" % dest_path)
                        os.link(dest_path, tmp_path)
                    else:
                        self.get_file(file_path, tmp_path)
                        
        
                # Get SRPMS for i386 tasks only
                if not task['target']['arch_label'] == 'i386':
                    continue
                    
                for _file in task['sources']:
                    dest_path = os.path.join(task['srpm_path'], _file)
                    tmp_path = os.path.join(task['tmp_srpm_path'], _file)
                    file_path = '%s/sources/%s' % (task['fs_path'], _file)
                    
                    # Create a hardlink if it existes prevously
                    if os.path.exists(dest_path):
                        log.debug("Hard linking from: %s" % dest_path)
                        os.link(dest_path, tmp_path)
                        continue
                    else:
                        self.get_file(file_path, tmp_path)
        
        # GPG and EUA
        if os.path.exists(self.gpg_key_path):
            dest = os.path.join(self.tmp_path, 'IUS-COMMUNITY-GPG-KEY')
            log.info("Updating IUS-COMMUNITY-GPG-KEY") 
            if os.path.exists(dest):
                os.remove(dest)
            shutil.copy(self.gpg_key_path, dest)
        if os.path.exists(self.eua_path):
            dest = os.path.join(self.tmp_path, 'IUS-COMMUNITY-EUA')
            log.info("Updating IUS-COMMUNITY-EUA") 
            if os.path.exists(dest):
                os.remove(dest)
            shutil.copy(self.eua_path, dest)
                
        # create current hash
        _hash = hashlib.md5(datetime.now().__str__()).hexdigest()
        current = os.path.join(self.tmp_path, 'CURRENT')
        log.info("Updating CURRENT file with hash: %s" % _hash)
        f = open(current, 'w+')
        f.write(_hash)
        f.close()

        # move new dir into place
        if os.path.exists(self.local_path):
            shutil.rmtree(self.local_path)
        log.debug("Moving %s -> %s" % (self.tmp_path, self.local_path))
        shutil.move(self.tmp_path, self.local_path)
        
    def sync_with_remote(self, remote_path, delete=False):
        pass
        
    def build_metadata(self):
        """
        Generate Yum metadata in each director of path_list.

        """
        path_list = self.get_repo_paths(self.local_path)
            
        log.info("Generating repository metadata")
        config = get_config()
        start = len(config['admin']['repo_base_path'].split('/'))
        for path in path_list:
            log.info("  `-> %s" % '/'.join(path.split('/')[start:]))
            if 'debuginfo' in path.split('/'):
                os.system('%s -d -s md5 %s >/dev/null' % \
                    (self.config['admin']['createrepo_binpath'], path))
            else:
                os.system('%s -x debuginfo -d -s md5 %s >/dev/null' % \
                    (self.config['admin']['createrepo_binpath'], path))
            
            # run yum-arch for el4 repos
            if path.find('Redhat/4/') > 0:
                os.system('%s %s >/dev/null 2>&1' % \
                    (self.config['admin']['yumarch_binpath'], path))
                    
            # add repoview
            os.system('%s %s >/dev/null 2>&1' % \
                    (self.config['admin']['repoview_binpath'], path))
                    
    def sign_package(self, path):
        if not os.path.exists(path):
            log.warn("Path does not exist: %s" % path)
            return
            
        log.debug("Signing %s" % path)        
        cmd = "%s --resign %s" % \
              (self.config['rpm_binpath'], path)
        try:
            log.debug("Executing: %s" % cmd)
            child = pexpect.spawn(cmd)
            child.expect('Enter pass phrase: ')
            child.sendline(self.gpg_passphrase)
            child.wait()
            if child.exitstatus != 0:
                log.fatal("Failed signing %s" % path)
        except pexpect.EOF, e:
            log.warn('Caught pexpect.EOF???')
        except pexpect.TIMEOUT, e:
            log.warn('Caught pexpect.TIMEOUT???')
                    