#!/usr/bin/env python3
from csv import DictReader
from logging import basicConfig, error, info
from os import environ, listdir, makedirs, walk
from os.path import abspath, basename, dirname, isfile, join
from random import seed, shuffle
from re import fullmatch
from shutil import rmtree
from subprocess import CalledProcessError, check_output, DEVNULL, run
from sys import argv, exit, path
path.insert(1, dirname(dirname(abspath(__file__))))
from common import RANDOM_SEED, TOOLS, LOG_CONFIG

GIT_URL = 'https://github.com/%s.git'
EXCLUDE = [[r'.*\.java', r'\s*import\s+(javax\.microedition|(com\.(google\.)?)?android|androidx)\..*'],
           [r'AndroidManifest\.xml', r'.*']]

def create_dataset(github_csv, output_dir, project_count):
    basicConfig(**LOG_CONFIG)
    seed(RANDOM_SEED)
    makedirs(output_dir, exist_ok=True)
    if listdir(output_dir):
        print(f"Directory {output_dir} is not empty")
        exit(1)

    with open(github_csv) as in_file:
        reader = DictReader(in_file)
        projects = [row for row in reader if row['license'] != 'Other']
        shuffle(projects)

        included = 0
        hashes = set()
        for project in projects:
            if create_project(project, output_dir, hashes):
                included += 1
                if included == project_count:
                    break
            else:
                delete_project(project, output_dir)

def create_project(project, output_dir, hashes):
    info("Cloning " + project['name'])
    project_dir = clone_repo(project, output_dir)
    return (project_dir is not None
            and has_tool(project_dir)
            and not project_is_duplicate(project_dir, hashes)
            and not project_has_excluded_technology(project_dir))

def delete_project(project, output_dir):
    rmtree(get_project_dir(project, output_dir), ignore_errors=True)

def get_project_dir(project, output_dir):
    return join(output_dir, project['name'].replace('/', '_'))

def clone_repo(project, output_dir):
    url = GIT_URL % project['name']
    project_dir = get_project_dir(project, output_dir)

    try:
        run(['git', 'clone', '--depth=1', url, project_dir], stdin=DEVNULL, stdout=DEVNULL,
            stderr=DEVNULL, env=environ | {'GIT_TERMINAL_PROMPT': '0'}, check=True)
        return project_dir
    except CalledProcessError:
        return None

def has_tool(project_dir):
    for tool in TOOLS:
        if any(isfile(join(project_dir, file)) for file in tool.files):
            return True
    return False

def project_is_duplicate(project_dir, hashes):
    command = 'git ls-files --format="%(objectname) %(path)" | git hash-object --stdin'
    project_hash = check_output(command, shell=True, cwd=project_dir).decode().strip()

    if project_hash in hashes:
        return True
    else:
        hashes.add(project_hash)
        return False

def project_has_excluded_technology(project_dir):
    for root, dirs, files in walk(project_dir):
        for file in files:
            for name, content in EXCLUDE:
                if file_matches(join(root, file), name, content):
                    return True
    return False

def file_matches(file, name, content):
    if fullmatch(name, basename(file)):
        try:
            with open(file, encoding='ascii', errors='ignore') as f:
                if any(fullmatch(content, line.rstrip()) for line in f):
                    return True
        except FileNotFoundError as e:
            error(e)
            return True
    return False

if __name__ == '__main__':
    if len(argv) == 4 and argv[3].isdigit():
        create_dataset(argv[1], argv[2], int(argv[3]))
    else:
        print(f"Usage: {basename(__file__)} <github.csv> <output_dir> <project_count>")
