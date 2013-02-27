#!/usr/bin/env python
import os
from git import Repo
from git.repo.fun import is_git_dir
import csv

def list_repos():
    target_list = os.listdir('.')
    while target_list:
        dirname = target_list.pop(0)
        if not os.path.isdir(dirname):
            continue

        if not is_git_dir(os.path.join(dirname, '.git')):
            for next_dir in os.listdir(dirname):
                target_list.append(os.path.join(dirname, next_dir))
            continue
        repo = Repo(dirname)

        for remote in repo.remotes:
            if remote.name == 'origin':
                yield (dirname, remote.url)

def load_repos_list(path):
    for row in csv.reader(open(path)):
        yield tuple(row)

def clone_repos():
    saved_repos = set(load_repos_list('repositories.csv'))
    current_repos = set(list_repos())
    for path, url in saved_repos - current_repos:
        print 'clone %s to %s' % (url, path)
        repos_dir = os.path.join('/Users/kenjif/new_repo', path)
        kargs = {'separate-git-dir' : repos_dir}
        Repo.clone_from(url, path, None, **kargs)

def update_repos_list():
    saved_repos = set(load_repos_list('repositories.csv'))
    current_repos = set(list_repos())

    writer = csv.writer(open('repositories.csv', 'w'))
    for row in current_repos | saved_repos:
        writer.writerow(row)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Git Repository Manager')
    subparsers = parser.add_subparsers()

    sub_parser = subparsers.add_parser('clone')
    sub_parser.set_defaults(func=clone_repos)

    args = parser.parse_args()
    args.func()
    
