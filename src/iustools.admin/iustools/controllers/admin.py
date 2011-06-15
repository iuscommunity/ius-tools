"""Admin controller class to expose commands for iustools."""

import re
import os
import hashlib
import shutil
from datetime import datetime
from urllib import urlopen
from cement.core.log import get_logger
from cement.core.namespace import get_config

from iustools.core.controller import IUSToolsController, expose
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
                    config['admin']['repo_base_path'],
                    tag_label,
                    task['target']['tag_path']
                    )
                tasks.append(task)
        return tasks
                
    @expose(namespace='admin')              
    def gen_repo(self):
        repo_paths = []
        orig_dir = os.curdir

        if self.cli_opts.clean:
            if os.path.exists(config['admin']['repo_base_path']):
                log.debug('Removing existing repo %s' % \
                    config['admin']['repo_base_path'])
                shutil.rmtree(config['admin']['repo_base_path'])


        log.info('Generating ius repository in %s' %
                 config['admin']['repo_base_path'])
        if self.cli_opts.tag_label:
            tags = self.cli_opts.tag_label.split(',')
        else:
            tags = config['admin']['managed_tags']

        for tag_label in tags:
            log.info("Processing tag %s" % tag_label)
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

        # createrepos
        log.info("Generating repository metadata")
        for path in repo_paths:
            os.system('createrepo -s md5 %s' % path)

        # create current hash
        f = open(os.path.join(config['admin']['repo_base_path'], 'CURRENT'), 'w+')
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

