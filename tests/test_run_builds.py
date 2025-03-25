from os import linesep
from pathlib import Path
from sys import path
from tempfile import TemporaryDirectory
from unittest import main, TestCase
from common import RESULTS_CSV
path.insert(1, str((Path(__file__).parent / '..' / 'execution').resolve()))
rb = __import__('run-builds')

class TestRunBuilds(TestCase):
    def test_volume_name_is_user_friendly(self):
        cache_dir = '/root/.tool/cache'
        volume_name = rb.get_volume_name(cache_dir)
        self.assertIn('_root_tool_cache', volume_name)

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

if __name__ == '__main__':
    main()
