from csv import DictReader
from pathlib import Path
from subprocess import run, DEVNULL
from sys import executable
from tempfile import TemporaryDirectory
from unittest import main, TestCase
from common import MAX_JAVA, MIN_JAVA, RESULTS_CSV

class TestEnvironment(TestCase):
    @classmethod
    def setUpClass(cls):
        build_images = (Path(__file__).parent / '..' / 'environment' / 'build-images.py').resolve()
        run([executable, build_images], stdout=DEVNULL, stderr=DEVNULL, check=True)

    def test_always_passing_projects_pass_for_each_java_version(self):
        with TemporaryDirectory() as results_dir:
            script = (Path(__file__).parent / '..' / 'execution' / 'run-builds.py').resolve()
            dataset_dir = Path(__file__).parent / 'pass-all'
            result = run([executable, script, dataset_dir, results_dir, results_dir])
            self.assertEqual(result.returncode, 0)

            with open(Path(results_dir) / RESULTS_CSV, 'r') as results_file:
                reader = DictReader(results_file)
                for project in reader:
                    for java_version in range(MIN_JAVA, MAX_JAVA + 1):
                        self.assertEqual(project[f'java{java_version}'], '0',
                                         f"Java {java_version} {project['name']} failed")
                self.assertEqual(reader.line_num, len(list(dataset_dir.iterdir())) + 1,
                                 "Wrong project count in CSV")

            for project_dir in dataset_dir.iterdir():
                log_dir = Path(results_dir) / project_dir.name
                log_files = {file.name for file in log_dir.iterdir()}
                for java_version in range(MIN_JAVA, MAX_JAVA + 1):
                    self.assertIn(f'{java_version:02d}.pass', log_files)

if __name__ == '__main__':
    main()
