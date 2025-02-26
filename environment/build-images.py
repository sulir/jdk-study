#!/usr/bin/env python3
from os.path import dirname, realpath
from pty import spawn
from sys import exit

MIN_JAVA = 6
MAX_JAVA = 23
VERSIONS = {
    'Zulu': {6: '6.22.0.3', 7: '7.56.0.11', 8: '8.84.0.15', 9: '9.0.7.1', 10: '10.3.5', 11: '11.78.15',
             12: '12.3.11', 13: '13.54.17', 14: '14.29.23', 15: '15.46.17', 16: '16.32.15', 17: '17.56.15',
             18: '18.32.13', 19: '19.32.13', 20: '20.32.11', 21: '21.40.17', 22: '22.32.15', 23: '23.32.11'},
    'JDK': {6: '6.0.119', 7: '7.0.352', 8: '8.0.442', 9: '9.0.7', 10: '10.0.2', 11: '11.0.26',
            12: '12.0.2', 13: '13.0.14', 14: '14.0.2', 15: '15.0.10', 16: '16.0.2', 17: '17.0.14',
            18: '18.0.2.1', 19: '19.0.2', 20: '20.0.2', 21: '21.0.6', 22: '22.0.2', 23: '23.0.2'},
    'Gradle': {6: '2.14.1', 7: '4.10.3', 8: '8.13'},
    'Maven': {6: '3.2.5', 7: '3.8.8', 8: '3.9.9'},
    'Ant': {6: '1.9.16', 8: '1.10.15'},
    'Ivy': {6: '2.4.0', 7: '2.5.3'},
    'Bouncy_Castle': {6: '1.67', 7: ''},
}
IMAGE_NAME = 'sulir/jdk-study'

def build_all_images():
    for java_version in range(MIN_JAVA, MAX_JAVA + 1):
        print(f"\nBuilding image for Java {java_version}...\n")
        if not build_image(java_version):
            exit(1)

def build_image(java_version):
    command = ['docker', 'build']
    for software, versions in VERSIONS.items():
        version = get_version(software, java_version)
        command += '--build-arg', '%s=%s' % (software.upper(), version)
    context_dir = dirname(realpath(__file__))
    command += '--tag', '%s:%d' % (IMAGE_NAME, java_version), context_dir

    return spawn(command) == 0

def get_version(software, java_version):
    versions = VERSIONS[software]

    while java_version >= MIN_JAVA:
        result = versions.get(java_version)
        if result is not None:
            return result
        java_version -= 1

    raise KeyError(f"No {software} version found for Java {java_version}")

if __name__ == '__main__':
    build_all_images()
