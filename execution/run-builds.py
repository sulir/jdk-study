#!/usr/bin/env python3
from csv import DictReader, DictWriter
from logging import basicConfig, info
from os import rename, scandir
from os.path import abspath, basename, dirname, isfile, join
from pathlib import Path
from random import seed, shuffle
from re import sub
from subprocess import DEVNULL, check_output, run, STDOUT
from sys import argv, path
from zlib import crc32
path.insert(1, dirname(dirname(abspath(__file__))))
from common import IMAGE_NAME, LOG_CONFIG, MIN_JAVA, MAX_JAVA, RANDOM_SEED, TOOLS

RESULTS_CSV = 'results.csv'
CACHE_DIRS = ['/root/.gradle/caches/modules-2/files-2.1', '/root/.gradle/wrapper/dists',
              '/root/.m2/repository', '/root/.m2/wrapper',
              '/root/.ivy2/cache']
DOCKER_PROJECT_SRC = '/mnt/project'

def run_builds(dataset_dir, results_dir):
    basicConfig(**LOG_CONFIG)
    remove_cache_volumes()
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    Path(results_dir, RESULTS_CSV).touch()

    project_dirs = sorted([file.path for file in scandir(dataset_dir) if file.is_dir()])
    seed(RANDOM_SEED)
    shuffle(project_dirs)
    project_dirs = remaining_projects(project_dirs, results_dir)

    with open(join(results_dir, RESULTS_CSV), 'a') as out_file:
        versions_header = ['java%d' % v for v in range(MIN_JAVA, MAX_JAVA + 1)]
        # noinspection PyTypeChecker
        writer = DictWriter(out_file, ['name', 'commit', 'tool', 'wrapper'] + versions_header)
        if out_file.tell() == 0:
            writer.writeheader()

        for project_dir in project_dirs:
            project_name = get_project_name(project_dir)
            result = build_project(project_name, project_dir, results_dir)
            writer.writerow(result)
            out_file.flush()
            remove_cache_volumes()

def remove_cache_volumes():
    for cache_dir in CACHE_DIRS:
        volume = get_volume_name(cache_dir)
        if run(['docker', 'volume', 'inspect', volume], stdout=DEVNULL, stderr=DEVNULL).returncode == 0:
            run(['docker', 'volume', 'rm', volume], stdout=DEVNULL, check=True)

def get_volume_name(cache_dir):
    name = sub(r'\W+', '_', IMAGE_NAME + cache_dir)
    return '%s_%08x' % (name, crc32(name.encode()))

def remaining_projects(project_dirs, results_dir):
    with open(join(results_dir, RESULTS_CSV), 'r') as results_file:
        reader = DictReader(results_file)
        finished = {project['name'] for project in reader}

    return [p_dir for p_dir in project_dirs if get_project_name(p_dir) not in finished]

def get_project_name(project_dir):
    return basename(project_dir).replace('_', '/', 1)

def build_project(project_name, project_dir, results_dir):
    info("Analyzing %s", project_name)
    builder, result = analyze_project(project_name, project_dir)
    log_dir = prepare_log_dir(project_dir, results_dir)

    java_versions = list(range(MIN_JAVA, MAX_JAVA + 1))
    seed(project_name)
    shuffle(java_versions)
    for java_version in java_versions:
        info("Building %s with Java %d", project_name, java_version)
        exitcode = build_project_with_java(project_dir, java_version, builder, log_dir)
        result[f'java{java_version}'] = exitcode

    return result

def analyze_project(project_name, project_dir):
    commit = get_commit(project_dir)
    tool = detect_tool(project_dir)
    wrapper = detect_wrapper(project_dir, tool)
    result = {'name': project_name, 'commit': commit, 'tool': tool.name, 'wrapper': wrapper}
    builder = tool.command if wrapper is None else wrapper
    return builder, result

def prepare_log_dir(project_dir, results_dir):
    log_dir = Path(results_dir, basename(project_dir))
    log_dir.mkdir(exist_ok=True)
    for file in log_dir.iterdir():
        if file.is_file():
            file.unlink()
    return str(log_dir)

def get_commit(project_dir):
    return check_output(['git', 'rev-parse', 'HEAD'], cwd=project_dir).decode().strip()

def detect_tool(project_dir):
    for tool in TOOLS:
        if any(isfile(join(project_dir, file)) for file in tool.files):
            return tool
    raise FileNotFoundError(f"No build script found in {project_dir}")

def detect_wrapper(project_dir, tool):
    if isfile(join(project_dir, tool.wrapper)):
        return tool.wrapper
    else:
        return None

def build_project_with_java(project_dir, java_version, builder, log_dir):
    volume_args = []
    for cache_dir in CACHE_DIRS:
        volume_args += ['--mount', 'type=volume,src=%s,dst=%s' % (get_volume_name(cache_dir), cache_dir)]
    command = ['docker', 'run', '--rm', '-q',
               '--mount', f'type=bind,src={project_dir},dst={DOCKER_PROJECT_SRC},readonly',
               *volume_args,
               f'{IMAGE_NAME}:{java_version}', builder]

    log_path = join(log_dir, '%02d' % java_version)
    with open(log_path, 'w') as log_file:
        exitcode = run(command, stdin=DEVNULL, stdout=log_file, stderr=STDOUT, bufsize=0).returncode

    rename(log_path, log_path + ('.pass' if exitcode == 0 else '.fail'))
    return exitcode

if __name__ == '__main__':
    if len(argv) == 3:
        run_builds(argv[1], argv[2])
    else:
        print("Usage: %s <dataset_dir> <results_dir>" % basename(__file__))
