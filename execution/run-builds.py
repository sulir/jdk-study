#!/usr/bin/env python3
from csv import DictWriter
from logging import basicConfig, info
from os import scandir, makedirs, rename
from os.path import abspath, basename, dirname, isfile, join
from random import seed, shuffle
from subprocess import DEVNULL, check_output, run, STDOUT
from sys import argv, path
path.insert(1, dirname(dirname(abspath(__file__))))
from common import IMAGE_NAME, LOG_CONFIG, MIN_JAVA, MAX_JAVA, RANDOM_SEED, TOOLS

RESULTS_CSV = 'results.csv'
DOCKER_PROJECT_SRC = '/mnt/project'

def run_builds(dataset_dir, results_dir):
    basicConfig(**LOG_CONFIG)
    seed(RANDOM_SEED)

    project_dirs = sorted([file.path for file in scandir(dataset_dir) if file.is_dir()])
    shuffle(project_dirs)
    makedirs(results_dir, exist_ok=True)

    with open(join(results_dir, RESULTS_CSV), 'w') as out_file:
        versions_header = ['java%d' % v for v in range(MIN_JAVA, MAX_JAVA + 1)]
        # noinspection PyTypeChecker
        writer = DictWriter(out_file, ['name', 'commit', 'tool', 'wrapper'] + versions_header)
        writer.writeheader()

        for project_dir in project_dirs:
            project_name = get_project_name(project_dir)
            result = build_project(project_name, project_dir, results_dir)
            writer.writerow(result)
            out_file.flush()

def get_project_name(project_dir):
    return basename(project_dir).replace('_', '/', 1)

def build_project(project_name, project_dir, results_dir):
    info('Analyzing ' + project_name)
    commit = get_commit(project_dir)
    tool = detect_tool(project_dir)
    wrapper = detect_wrapper(project_dir, tool)
    result = {'name': project_name, 'commit': commit, 'tool': tool.name, 'wrapper': wrapper}
    builder = tool.command if wrapper is None else wrapper

    java_versions = list(range(MIN_JAVA, MAX_JAVA + 1))
    shuffle(java_versions)
    for java_version in java_versions:
        info('Building %s with Java %d' % (project_name, java_version))
        exitcode = build_project_with_java(project_dir, java_version, builder, results_dir)
        result['java%d' % java_version] = exitcode

    return result

def get_commit(project_dir):
    return check_output(['git', 'rev-parse', 'HEAD'], cwd=project_dir).decode().strip()

def detect_tool(project_dir):
    for tool in TOOLS:
        if any(isfile(join(project_dir, file)) for file in tool.files):
            return tool
    return None

def detect_wrapper(project_dir, tool):
    if isfile(join(project_dir, tool.wrapper)):
        return tool.wrapper
    else:
        return None

def build_project_with_java(project_dir, java_version, builder, results_dir):
    log_path = join(results_dir, basename(project_dir), '%02d' % java_version)
    makedirs(dirname(log_path), exist_ok=True)
    command = ['docker', 'run', '--rm', '-q',
               '--mount', 'type=bind,src=%s,dst=%s,readonly' % (project_dir, DOCKER_PROJECT_SRC),
               '%s:%d' % (IMAGE_NAME, java_version), builder]

    with open(log_path, 'w') as log_file:
        exitcode = run(command, stdin=DEVNULL, stdout=log_file, stderr=STDOUT, bufsize=0).returncode

    rename(log_path, log_path + ('.pass' if exitcode == 0 else '.fail'))
    return exitcode

if __name__ == '__main__':
    if len(argv) == 3:
        run_builds(argv[1], argv[2])
    else:
        print('Usage: %s <dataset_dir> <results_dir>' % basename(__file__))
