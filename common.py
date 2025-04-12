from collections import namedtuple
import csv
from pathlib import Path
from logging import INFO

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
ARGS_FILE = Path(__file__).parent / '.args'

def read_arg(key, prompt=None, force=False):
    config = {'delimiter': '=', 'quoting': csv.QUOTE_NONE, 'quotechar': None, 'escapechar': '\\'}
    try:
        with open(ARGS_FILE) as file:
            reader = csv.reader(file,  **config)
            args = {key: value for key, value in reader}
    except IOError:
        args = {}

    if force:
        args.pop(key, None)

    if key in args:
        return args[key]
    else:
        value = input(f"Enter argument {key}: " if prompt is None else prompt)
        with open(ARGS_FILE, 'w') as file:
            writer = csv.writer(file, **config)
            writer.writerows([(k, v) for k, v in args.items()] + [(key, value)])
