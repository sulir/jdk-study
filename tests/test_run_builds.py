from os import linesep
from pathlib import Path
from sys import path
from tempfile import TemporaryDirectory
from unittest import main, TestCase
from common import RESULTS_CSV, Tool
path.insert(1, str((Path(__file__).parent / '..' / 'execution').resolve()))
rb = __import__('run-builds')

class TestRunBuilds(TestCase):
    def test_volume_name_is_user_friendly(self):
        cache_dir = '/root/.tool/cache'
        volume_name = rb.get_volume_name(cache_dir)
        self.assertRegex(volume_name, 'root.*tool.*cache')

    def test_volume_names_are_unique(self):
        cache_dirs = ['/root/tool/cache', '/root/.tool/cache', '/root/_tool/cache']
        volume_names = [rb.get_volume_name(cache_dir) for cache_dir in cache_dirs]
        self.assertEqual(len(volume_names), len(set(volume_names)))

    def test_csv_is_prepared_if_absent(self):
        with TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir) / 'results'
            csv_path = rb.prepare_results_csv(results_dir, ['field1', 'field2'])
            self.assertEqual(csv_path.parent, results_dir)
            self.assertEqual(csv_path.read_text(), 'field1,field2' + linesep)

    def test_csv_is_prepared_if_empty(self):
        with TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            (results_dir / RESULTS_CSV).touch()
            csv_path = rb.prepare_results_csv(results_dir, ['field1'])
            self.assertEqual(csv_path.parent, results_dir)
            self.assertEqual(csv_path.read_text(), 'field1' + linesep)

    def test_csv_is_intact_if_not_empty(self):
        with TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            original = 'field1,field2' + linesep + 'value1,value2' + linesep
            (results_dir / RESULTS_CSV).write_text(original)
            csv_path = rb.prepare_results_csv(results_dir, ['new'])
            self.assertEqual(csv_path.parent, results_dir)
            self.assertEqual(csv_path.read_text(), original)

    def test_pending_projects_for_empty_results_are_all(self):
        dataset_dir = Path(__file__).parent / 'pending'
        pending = set(rb.list_pending_projects(dataset_dir, dataset_dir / 'empty.csv'))
        expected = {dataset_dir / 'project_1', dataset_dir / 'project_2', dataset_dir / 'project_3'}
        self.assertEqual(pending, expected)

    def test_pending_projects_for_partial_results_are_remaining(self):
        dataset_dir = Path(__file__).parent / 'pending'
        pending = set(rb.list_pending_projects(dataset_dir, dataset_dir / 'partial.csv'))
        self.assertEqual(pending, {dataset_dir / 'project_2'})

    def test_pending_projects_for_full_results_are_none(self):
        dataset_dir = Path(__file__).parent / 'pending'
        pending = set(rb.list_pending_projects(dataset_dir, dataset_dir / 'full.csv'))
        self.assertEqual(pending, set())

    def test_get_project_name_works_with_absolute_path(self):
        self.assertEqual(rb.get_project_name(Path('/proj/dir/owner_repo')), 'owner/repo')

    def test_get_project_name_works_with_relative_path(self):
        self.assertEqual(rb.get_project_name(Path('proj/dir/owner_repo')), 'owner/repo')

    def test_get_project_name_works_with_special_characters(self):
        self.assertEqual(rb.get_project_name(Path('dir/ow-ner__r-e.p0')), 'ow-ner/_r-e.p0')

    def test_prepare_log_dir_creates_empty_directory(self):
        with TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            project_dir = Path('project_dir')
            log_dir = rb.prepare_log_dir(project_dir, results_dir)
            self.assertEqual(list(log_dir.iterdir()), [])
            self.assertEqual(log_dir.parent, results_dir)

    def test_prepare_log_dir_removes_existing_files(self):
        with TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir)
            project_dir = Path('project_dir')
            log_dir = rb.prepare_log_dir(project_dir, results_dir)
            (log_dir / '06.pass').touch()
            log_dir = rb.prepare_log_dir(project_dir, results_dir)
            self.assertEqual(list(log_dir.iterdir()), [])
            self.assertEqual(log_dir.parent, results_dir)

    def test_highest_priority_tool_is_detected(self):
        tools = {('build.gradle', 'pom.xml', 'build.xml'): 'Gradle',
                 ('settings.gradle', 'pom.xml', 'build.xml'): 'Gradle',
                 ('build.gradle.kts', 'pom.xml', 'build.xml'): 'Gradle',
                 ('settings.gradle.kts', 'pom.xml', 'build.xml'): 'Gradle',
                 ('pom.xml', 'build.xml'): 'Maven',
                 ('build.xml', 'other_file'): 'Ant'}
        for files, tool_name in tools.items():
            with TemporaryDirectory() as temp_dir:
                project_dir = Path(temp_dir)
                for file in files:
                    (project_dir / file).touch()
                self.assertEqual(rb.detect_tool(project_dir).name, tool_name,
                                 f"Detection failed for {files}")

    def test_tool_detection_fails_without_build_script(self):
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(FileNotFoundError):
                rb.detect_tool(Path(temp_dir))

    def test_wrapper_is_detected_if_present(self):
        tools = [Tool('Gradle', None, None, 'gradlew'),
                 Tool('Maven', None, None, 'mvnw'),
                 Tool('Ant', None, None, 'antw')]
        for tool in tools:
            with TemporaryDirectory() as temp_dir:
                project_dir = Path(temp_dir)
                for wrapper in [t.wrapper for t in tools]:
                    (project_dir / wrapper).touch()
                self.assertEqual(rb.detect_wrapper(project_dir, tool), tool.wrapper)

    def test_wrapper_is_none_if_absent(self):
        tool = Tool('Name', None, None, 'wrapper')
        with TemporaryDirectory() as temp_dir:
            self.assertIsNone(rb.detect_wrapper(Path(temp_dir), tool))

if __name__ == '__main__':
    main()
