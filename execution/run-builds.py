#!/usr/bin/env python3
from csv import DictReader, DictWriter
from logging import basicConfig, info
from pathlib import Path
from random import seed, shuffle
from re import sub
from signal import SIGINT, signal, SIGTERM
from subprocess import DEVNULL, check_output, run, STDOUT
from sys import argv, exit, path
from zlib import crc32
path.insert(1, str(Path(__file__).resolve().parent.parent))
from common import IMAGE_NAME, LOG_CONFIG, MAX_JAVA, MIN_JAVA, RANDOM_SEED, RESULTS_CSV, TOOLS

CACHE_DIRS = ['/root/.gradle/caches/modules-2/files-2.1', '/root/.gradle/wrapper/dists',
              '/root/.m2/repository', '/root/.m2/wrapper',
              '/root/.ivy2/cache']
DOCKER_PROJECT_SRC = '/mnt/project'

def run_builds(dataset_dir, results_dir):
    initialize()
    csv_fields = ['name', 'commit', 'tool', 'wrapper'] + [f'java{v}' for v in range(MIN_JAVA, MAX_JAVA + 1)]
    results_csv = prepare_results_csv(results_dir, csv_fields)
    project_dirs = list_pending_projects(dataset_dir, results_csv)

    with open(results_csv, 'a') as out_file:
        writer = DictWriter(out_file, csv_fields) # type: ignore
        for project_dir in project_dirs:
            project_name = get_project_name(project_dir)
            result = build_project(project_name, project_dir, results_dir)
            writer.writerow(result)
            out_file.flush()
            remove_cache_volumes()

def initialize():
    basicConfig(**LOG_CONFIG)
    for sig in (SIGINT, SIGTERM):
        signal(sig, handle_exit)
    remove_cache_volumes()

def remove_cache_volumes():
    for cache_dir in CACHE_DIRS:
        volume = get_volume_name(cache_dir)
        if run(['docker', 'volume', 'inspect', volume], stdout=DEVNULL, stderr=DEVNULL).returncode == 0:
            run(['docker', 'volume', 'rm', volume], stdout=DEVNULL, check=True)

def get_volume_name(cache_dir):
    name = sub(r'\W+', '_', IMAGE_NAME + cache_dir)
    return '%s_%08x' % (name, crc32(name.encode()))

def prepare_results_csv(results_dir, fields):
    results_dir.mkdir(parents=True, exist_ok=True)
    csv_path = results_dir / RESULTS_CSV
    with open(csv_path, 'a') as out_file:
        writer = DictWriter(out_file, fields) # type: ignore
        if out_file.tell() == 0:
            writer.writeheader()
    return csv_path

def list_pending_projects(dataset_dir, results_csv):
    project_dirs = sorted([file for file in dataset_dir.iterdir() if file.is_dir()])
    seed(RANDOM_SEED)
    shuffle(project_dirs)

    with open(results_csv, 'r') as results_file:
        reader = DictReader(results_file)
        finished = {project['name'] for project in reader}

    return [p_dir for p_dir in project_dirs if get_project_name(p_dir) not in finished]

def get_project_name(project_dir):
    return project_dir.name.replace('_', '/', 1)

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
    log_dir = results_dir / project_dir.name
    log_dir.mkdir(exist_ok=True)
    for file in log_dir.iterdir():
        if file.is_file():
            file.unlink()
    return log_dir

def get_commit(project_dir):
    return check_output(['git', 'rev-parse', 'HEAD'], cwd=project_dir).decode().strip()

def detect_tool(project_dir):
    for tool in TOOLS:
        if any((project_dir / file).is_file() for file in tool.files):
            return tool
    raise FileNotFoundError(f"No build script found in {project_dir}")

def detect_wrapper(project_dir, tool):
    if (project_dir / tool.wrapper).is_file():
        return tool.wrapper
    else:
        return None

def build_project_with_java(project_dir, java_version, builder, log_dir):
    volumes = [f'--mount=type=volume,src={get_volume_name(cache)},dst={cache}' for cache in CACHE_DIRS]
    command = ['docker', 'run', '--rm', '--quiet', f'--name={get_container_name()}',
               f'--mount=type=bind,src={project_dir},dst={DOCKER_PROJECT_SRC},readonly',
               *volumes,
               f'{IMAGE_NAME}:{java_version}', builder]

    log = log_dir / ('%02d' % java_version)
    with open(log, 'w') as log_file:
        exitcode = run(command, stdin=DEVNULL, stdout=log_file, stderr=STDOUT, bufsize=0).returncode

    log.rename(log.with_suffix('.pass' if exitcode == 0 else '.fail'))
    return exitcode

def get_container_name():
    return IMAGE_NAME.replace('/', '_') + '_container'

def handle_exit(*_):
    run(['docker', 'stop', '--timeout=1', get_container_name()], stdout=DEVNULL, stderr=DEVNULL)
    exit(1)

if __name__ == '__main__':
    if len(argv) == 3:
        run_builds(Path(argv[1]), Path(argv[2]))
    else:
        print("Usage: %s <dataset_dir> <results_dir>" % Path(__file__).name)
