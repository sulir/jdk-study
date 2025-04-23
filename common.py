from collections import namedtuple
from logging import INFO
from pathlib import Path
from sys import argv, exit, stderr

LOG_CONFIG = {'level': INFO, 'format': '[%(asctime)s][%(levelname)s] %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
RANDOM_SEED = 4321

Tool = namedtuple('Tool', ['name', 'files', 'command', 'wrapper'])
TOOLS = [Tool('Gradle', ['build.gradle', 'build.gradle.kts',
                         'settings.gradle', 'settings.gradle.kts'], 'gradle', 'gradlew'),
         Tool('Maven', ['pom.xml'], 'mvn', 'mvnw'),
         Tool('Ant', ['build.xml'], 'ant', 'antw')]

MIN_JAVA = 6
MAX_JAVA = 23
IMAGE_NAME = 'sulir/jdk-study'
DOCKER_PROJECT_SRC = '/mnt/project'
RESULTS_CSV = 'results.csv'

def require_path_args(*args):
    if len(argv) == len(args) + 1:
        return map(Path, argv[1:])
    else:
        script_name = Path(argv[0]).name
        arg_names = ' '.join(f'<{a}>' for a in args)
        exit_notebook(f"Usage: marimo edit {script_name} {arg_names}")
        return []

def exit_notebook(message):
    print(message, file=stderr)
    from marimo import running_in_notebook, stop
    stop(True) if running_in_notebook() else exit(1)
