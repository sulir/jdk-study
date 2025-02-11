#!/usr/bin/env python3
from csv import DictReader, DictWriter
from os import walk
from os.path import join, isfile, basename
from random import shuffle
from re import fullmatch
from shutil import rmtree
from subprocess import run, DEVNULL, CalledProcessError, check_output
from sys import argv

PROJECT_COUNT = 2500
GIT_URL = 'https://github.com/%s.git'
OUTPUT_CSV = 'projects.csv'
TOOLS = {'build.gradle': 'Gradle', 'build.gradle.kts': 'Gradle', 'pom.xml': 'Maven', 'build.xml': 'Ant'}
EXCLUDE = [[r'.*\.java', 'import android.'], [r'AndroidManifest\.xml', ''],
           [r'.*\.java', 'import javax.microedition.'],
           [r'.*\.(c|cc|cpp|cxx)', 'JNIEXPORT']]

def create_dataset(github_csv, output_dir):
    with open(github_csv) as in_file, open(join(output_dir, OUTPUT_CSV), 'w') as out_file:
        reader = DictReader(in_file)
        # noinspection PyTypeChecker
        writer = DictWriter(out_file, ['name', 'commit', 'tool'])
        writer.writeheader()

        projects = [row for row in reader if row['license'] != 'Other']
        shuffle(projects)
        included = 0
        hashes = set()

        for project in projects:
            result = create_project(project, output_dir, hashes)
            if result is not None:
                writer.writerow(result)
                out_file.flush()
                included += 1
                if included == PROJECT_COUNT:
                    break
            else:
                delete_project(project, output_dir)

def create_project(project, output_dir, hashes):
    print(project['name'])
    project_dir, commit = clone_repo(project, output_dir)
    if project_dir is None:
        return None

    tool = detect_tool(project_dir)
    if tool is None:
        return None

    if project_is_duplicate(project_dir, hashes):
        return None

    if project_has_excluded_technology(project_dir):
        return None

    return {'name': project['name'], 'commit': commit, 'tool': tool}

def delete_project(project, output_dir):
    rmtree(get_project_dir(project, output_dir), ignore_errors=True)

def get_project_dir(project, output_dir):
    return join(output_dir, project['name'].replace('/', '_'))

def clone_repo(project, output_dir):
    url = GIT_URL % project['name']
    project_dir = get_project_dir(project, output_dir)

    try:
        run(['git', 'clone', '--depth=1', url, project_dir], stdout=DEVNULL, stderr=DEVNULL, check=True)
        commit = check_output(['git', 'rev-parse', 'HEAD'], cwd=project_dir).decode().strip()
        return project_dir, commit
    except CalledProcessError:
        return None, None

def detect_tool(project_dir):
    for file, tool in TOOLS.items():
        if isfile(join(project_dir, file)):
            return tool
    return None

def project_is_duplicate(project_dir, hashes):
    command = 'git ls-files --format="%(objectname) %(path)" | git hash-object --stdin'
    project_hash = check_output(command, shell=True, cwd=project_dir).decode()

    if project_hash in hashes:
        return True
    else:
        hashes.add(hash)
        return False

def project_has_excluded_technology(project_dir):
    for root, dirs, files in walk(project_dir):
        for file in files:
            if file_has_excluded_technology(join(root, file)):
                return True
    return False

def file_has_excluded_technology(file):
    for pattern, content in EXCLUDE:
        if fullmatch(pattern, basename(file)):
            with open(file, encoding='ascii', errors='ignore') as f:
                if content in f.read():
                    return True
    return False

if __name__ == '__main__':
    if len(argv) == 3:
        create_dataset(argv[1], argv[2])
    else:
        print("Usage: create-dataset.py <github.csv> <output_dir>")
