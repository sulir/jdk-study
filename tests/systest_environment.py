from pathlib import Path
from subprocess import DEVNULL, run
from sys import executable
from unittest import main, TestCase
from common import DOCKER_PROJECT_SRC, IMAGE_NAME, MIN_JAVA, MAX_JAVA, TOOLS

class TestEnvironment(TestCase):
    @classmethod
    def setUpClass(cls):
        build_images = (Path(__file__).parent / '..' / 'environment' / 'build-images.py').resolve()
        run([executable, build_images], stdout=DEVNULL, stderr=DEVNULL, check=True)

    def test_tools_pass_for_each_java_version(self):
        for tool in TOOLS:
            build_dir = Path(__file__).parent / 'pass-all' / f'{tool.command}_project'
            for java_version in range(MIN_JAVA, MAX_JAVA + 1):
                with self.subTest(tool=tool.name, java_version=java_version):
                    command = ['docker', 'run', '--rm',
                               f'--mount=type=bind,src={build_dir},dst={DOCKER_PROJECT_SRC},readonly',
                               f'{IMAGE_NAME}:{java_version}', tool.command]
                    result = run(command, stdout=DEVNULL, stderr=DEVNULL)
                    self.assertEqual(result.returncode, 0, f"Java {java_version} {tool.name} failed")

if __name__ == '__main__':
    main()
