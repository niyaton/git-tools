#!/usr/bin/env python
import os
from git import Repo
from git.repo.fun import is_git_dir
from git.repo.fun import read_gitfile
import csv
import tempfile
import shutil
from ConfigParser import SafeConfigParser

class Manager:
    def __init__(self, repo_db):
        self.repo_db = repo_db
        self.load_repo_db()

    def load_repo_db(self):
        parser = SafeConfigParser()
        parser.readfp(open(self.repo_db))
        
        path = parser.get('setting', 'worktree_root')
        self.worktree_root = os.path.realpath(os.path.expanduser(path))
        path = parser.get('setting', 'git_dirs_root')
        self.repo_root = os.path.realpath(os.path.expanduser(path))

        self.saved_repos = []
        for section in parser.sections():
            if section[0:5] != 'repo ':
                continue
            path = section[5:]
            self.saved_repos.append((path, parser.get(section, 'url')))

    def list_repos(self, verbose=False):
        if verbose:
            return self.list_repos_verbose()

        max_length = max([len(path) for path, url in self.saved_repos])
        for path, url in self.saved_repos:
            path = path.ljust(max_length)
            print " ".join((path, url))

    def list_repos_verbose(self):
       for path, url in self.saved_repos:
            print path
            print '\t[remote url]:', url
            try:
                git_dir = Repo(path).git_dir
                print '\t   [git_dir]:', Repo(path).git_dir
            except:
                print '\t   [git_dir]: not sotred'
 
    def check_stored(self):
       for path, url in self.saved_repos:
            try:
                git_dir = Repo(path).git_dir
            except:
                git_dir = None
            if not git_dir:
                print 'repo path %s is not stored.' % (path)

    def iter_unstored_repos(self):
        for path, url in self.saved_repos:
            try:
                git_dir = Repo(path).git_dir
            except:
                yield (path, url)

    def fix_unstored(self):
        for path, url in self.iter_unstored_repos():
            print '%s is not stored.' % (path)
                
            parent_dir, tail = os.path.split(path)

            repos_dir = os.path.join(self.repo_root, path)
            parent_dir, dummy = os.path.split(repos_dir)

            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
                
            if not self.check_dir_structure(parent_dir, self.repo_root):
                raise Exception('Invalid Directory Structure!')
            
            self.clone_unstored_repo(path, repos_dir, url)

    def check_dir_structure(self, path, until):
        while path != until:
            if not os.path.isdir(path):
                print '%s is not a directory!' % (path)
                return False
            if os.path.isdir(path) and is_git_repo(path):
                print "Wrong Repositories Structure! %s is a git repository." % (path)
                return False
            path, dummy = os.path.split(path)

        return True

    def clone_unstored_repo(self, worktree_path, git_dir, url):
        print 'clone repository %s from %s' % (worktree_path, url)
        tmp_dir = tempfile.mkdtemp()

        try:
            kargs = {'separate-git-dir' : git_dir}
            repo = Repo.clone_from(url, tmp_dir, None, **kargs)
            workingdir = os.path.join(self.worktree_root, worktree_path)
            repo.config_writer().set('core', 'worktree', workingdir)
        except:
            print 'clone is failed!'
        finally:
            shutil.rmtree(tmp_dir)

    def clone_new_repo(self, path, url):
        if any(p for p, url in self.saved_repos if p == path):
            print 'You already cloned %s' % (path)
            return

        worktree_path = os.path.join(self.worktree_root, path)
        git_dir = os.path.join(self.repo_root, path)

        worktree_parent, tail = os.path.split(worktree_path)
        if not self.check_dir_structure(worktree_parent, self.worktree_root):
            return

        git_dir_parent, tail = os.path.split(git_dir)
        if not self.check_dir_structure(git_dir_parent, self.repo_root):
            return

        if os.path.exists(worktree_path):
            print '%s is already exist' % (worktree_path)
            return

        if os.path.exists(git_dir):
            print '%s is already exist' % (git_dir)
            return

        if not os.path.exists(worktree_parent):
            os.makedirs(worktree_parent)
        
        if not os.path.exists(git_dir_parent):
            os.makedirs(git_dir_parent)

        print 'clone %s to %s' % (url, path)
        kargs = {'separate-git-dir' : git_dir}
        Repo.clone_from(url, worktree_path, None, **kargs)

        self.save_repo(url, path)

    def save_repo(self, path, url):
        parser = SafeConfigParser()
        with open(self.repo_db)  as f:
            parser.readfp(f)

        parser.add_section(path)
        parser.set(path, 'url', url)

        with open(self.repo_db, 'w') as f:
            parser.write(f)
    
def is_git_repo(path):
    git = os.path.join(path, '.git')
    return os.path.exists(git)

def list_repos_old():
    target_list = os.listdir('.')
    while target_list:
        dirname = target_list.pop(0)
        if not os.path.isdir(dirname):
            continue

        if not is_git_repo(os.path.join(dirname, '.git')):
            for next_dir in os.listdir(dirname):
                target_list.append(os.path.join(dirname, next_dir))
            continue
        repo = Repo(dirname)

        for remote in repo.remotes:
            if remote.name == 'origin':
                yield (dirname, remote.url)

def list_repos():
    target_list = os.listdir('.')
    while target_list:
        dirname = target_list.pop(0)
        if not os.path.isdir(dirname):
            continue

        gitfile = os.path.join(dirname, '.git')
        if not os.path.isfile(gitfile):
            for next_dir in os.listdir(dirname):
                target_list.append(os.path.join(dirname, next_dir))
            continue

        if read_gitfile(gitfile, '.') is None:
            continue

        repo = Repo(dirname)
        for remote in repo.remotes:
            if remote.name == 'origin':
                yield (dirname, remote.url)

def update_repos_list():
    saved_repos = set(load_repos_list('repositories.csv'))
    current_repos = set(list_repos())

    writer = csv.writer(open('repositories.csv', 'w'))
    for row in current_repos | saved_repos:
        writer.writerow(row)
       
def remove():
    saved_repos = set(load_repos_list('repositories.csv'))
    current_repos = set(list_repos())

    for path, url in current_repos - saved_repos:
        repo = Repo(path)
        print 'remove:', path, repo.git_dir
        shutil.rmtree(repo.git_dir)
        shutil.rmtree(path)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Git Repository Manager')
    manager = Manager('repos.conf')
    subparsers = parser.add_subparsers()

    sub_parser = subparsers.add_parser('fix')
    sub_parser.set_defaults(func= lambda args: manager.fix_unstored())
    sub_parser = subparsers.add_parser('list')
    sub_parser.add_argument('-v', '--verbose', action='store_true')
    sub_parser.set_defaults(func= lambda args: manager.list_repos(args.verbose))
    sub_parser = subparsers.add_parser('check')
    sub_parser.set_defaults(func= lambda args: manager.check_stored())
    sub_parser = subparsers.add_parser('convert')
    sub_parser.set_defaults(func= lambda args: manager.convert_csv2conf())
    sub_parser = subparsers.add_parser('clone')
    sub_parser.add_argument('path')
    sub_parser.add_argument('url')
    sub_parser.set_defaults(func= lambda args: manager.clone_new_repo(args.path, args.url))

    args = parser.parse_args()
    args.func(args)
    
