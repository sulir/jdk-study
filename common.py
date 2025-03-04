from collections import namedtuple

Tool = namedtuple('Tool', ['name', 'files', 'command', 'wrapper'])
TOOLS = [Tool('Gradle', ['build.gradle', 'build.gradle.kts'], 'gradle', 'gradlew'),
         Tool('Maven', ['pom.xml'], 'mvn', 'mvnw'),
         Tool('Ant', ['build.xml'], 'ant', 'antw')]

MIN_JAVA = 6
MAX_JAVA = 23
IMAGE_NAME = 'sulir/jdk-study'
