from collections import namedtuple
from logging import INFO

LOG_CONFIG = {'level': INFO, 'format': '[%(asctime)s][%(levelname)s] %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
RANDOM_SEED = 4321

Tool = namedtuple('Tool', ['name', 'files', 'command', 'wrapper'])
TOOLS = [Tool('Gradle', ['build.gradle', 'build.gradle.kts'], 'gradle', 'gradlew'),
         Tool('Maven', ['pom.xml'], 'mvn', 'mvnw'),
         Tool('Ant', ['build.xml'], 'ant', 'antw')]

MIN_JAVA = 6
MAX_JAVA = 23
IMAGE_NAME = 'sulir/jdk-study'
RESULTS_CSV = 'results.csv'
