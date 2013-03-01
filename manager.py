#!/usr/bin/env python
import os
from git import Repo
from git.repo.fun import is_git_dir
from git.repo.fun import read_gitfile
import csv
import tempfile
import shutil

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

def list_stored_repos(repos):
    repos_root = '/Users/kenjif/new_repo'
    for repo in repos:
        repo_dir = os.path.join(repos_root, repo)
        if is_git_dir(repo_dir):
            yield repo

def list_unstored_repos(repos):
    repos_root = '/Users/kenjif/new_repo'
    for repo in repos:
        repo_dir = os.path.join(repos_root, repo)
        if not is_git_dir(repo_dir):
            yield repo

def load_repos_list(path):
    for row in csv.reader(open(path)):
        yield tuple(row)

def clone_repos():
    saved_repos = set(load_repos_list('repositories.csv')) 
    current_repos = set(list_repos())
    print saved_repos
    print current_repos
    for path, url in saved_repos - current_repos:
        parent_dir, tail = os.path.split(path)
        curpath = parent_dir
        while curpath:
            if os.path.isdir(curpath) and is_git_repo(curpath):
                print "Wrong Repositories Structure! %s is a git repository." % (curpath)
                continue
            curpath, dummy = os.path.split(curpath)

        if parent_dir != '' and not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        
        repo_root = '/Users/kenjif/new_repo'
        repos_dir = os.path.join(repo_root, path)
        parent_dir, dummy = os.path.split(repos_dir)
        print parent_dir
        curpath = parent_dir
        while curpath != repo_root:
            if os.path.isdir(curpath) and is_git_repo(curpath):
                print "Wrong Repositories Structure! %s is a git repository." % (curpath)
                continue
            curpath, dummy = os.path.split(curpath)

        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        print 'clone %s to %s' % (url, path)
        print repos_dir
        kargs = {'separate-git-dir' : repos_dir}
        Repo.clone_from(url, path, None, **kargs)

def update_repos_list():
    saved_repos = set(load_repos_list('repositories.csv'))
    current_repos = set(list_repos())

    writer = csv.writer(open('repositories.csv', 'w'))
    for row in current_repos | saved_repos:
        writer.writerow(row)

def fix_dirty():
    saved_repos = [path for path, url in load_repos_list('repositories.csv')]
    unstored_repos = list(list_unstored_repos(saved_repos))

    saved_repos = set(load_repos_list('repositories.csv'))
    for path, url in saved_repos:
        if not path in unstored_repos:
            print '%s is already stored.' % (path)
            continue

        print '%s is not stored.' % (path)
            
        parent_dir, tail = os.path.split(path)

        repo_root = '/Users/kenjif/new_repo'
        repos_dir = os.path.join(repo_root, path)
        parent_dir, dummy = os.path.split(repos_dir)
        print parent_dir
        curpath = parent_dir
        while curpath != repo_root:
            if os.path.isdir(curpath) and is_git_repo(curpath):
                print "Wrong Repositories Structure! %s is a git repository." % (curpath)
                continue
            curpath, dummy = os.path.split(curpath)

        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        print 'clone bare repository %s from %s' % (path, url)
        tmp_dir = tempfile.mkdtemp()

        kargs = {'separate-git-dir' : repos_dir}
        repo = Repo.clone_from(url, tmp_dir, None, **kargs)
        worktree_root = '/Users/kenjif/Dropbox/new_repo'
        workingdir = os.path.join(worktree_root, path)
        repo.config_writer().set('core', 'worktree', workingdir)

        shutil.rmtree(tmp_dir)
        

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
    subparsers = parser.add_subparsers()

    sub_parser = subparsers.add_parser('clone')
    sub_parser.set_defaults(func=clone_repos)
    sub_parser = subparsers.add_parser('update')
    sub_parser.set_defaults(func=update_repos_list)
    sub_parser = subparsers.add_parser('fix')
    sub_parser.set_defaults(func=fix_dirty)
    sub_parser = subparsers.add_parser('remove')
    sub_parser.set_defaults(func=remove)

    args = parser.parse_args()
    args.func()
    
