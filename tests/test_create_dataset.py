from pathlib import Path
from re import fullmatch
from shutil import copytree
from sys import path
from tempfile import TemporaryDirectory
from unittest import main, TestCase
from common import TOOLS
path.insert(1, str((Path(__file__).parent / '..' / 'dataset').resolve()))
cd = __import__('create-dataset')

class TestCreateDataset(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.java_regex = next(pattern[1] for pattern in cd.EXCLUDE if fullmatch(pattern[0], 'X.java'))

    def test_java_exclusion_regex_should_match_android(self):
        matching = ['import android.app.Activity;',
                    'import androidx.appcompat.app.AppCompatActivity;',
                    'import com.android.systemui.statusbar.StatusBar;',
                    'import com.google.android.material.button.MaterialButton;',
                    ' import android.view.View',
                    '\timport android.view.View;',
                    'import  android.view.View;',
                    'import android.view.View; // comment']
        for line in matching:
            self.assertIsNotNone(fullmatch(self.java_regex, line))

    def test_java_exclusion_regex_should_match_javame(self):
        matching = ['import javax.microedition.midlet.MIDlet;'
                    'import javax.microedition.lcdui.Display;',
                    ' import javax.microedition.lcdui.Form;',
                    '\timport javax.microedition.lcdui.Form',
                    'import  javax.microedition.lcdui.Form;',
                    'import javax.microedition.lcdui.Form; // comment']
        for line in matching:
            self.assertIsNotNone(fullmatch(self.java_regex, line))

    def test_java_exclusion_regex_should_not_match_other(self):
        non_matching = ['import java.io.File;',
                        'import com.example.package.Class;',
                        ' import java.util.List',
                        '\timport  java.util.List;',
                        'import java.util.List; // comment',
                        '// import android.app.Activity;',
                        '"import android.app.Activity;"',
                        '//import javax.microedition.midlet.MIDlet;']
        for line in non_matching:
            self.assertIsNone(fullmatch(self.java_regex, line))

    def test_delete_project_should_delete_directory(self):
        source = Path(__file__).parent / 'delete'
        with TemporaryDirectory() as output_dir:
            copytree(source, output_dir, dirs_exist_ok=True)
            cd.delete_project({'name': 'owner/repo'}, output_dir)
            self.assertFalse((Path(output_dir) / 'owner_repo').exists())

    def test_get_project_dir_should_work_with_absolute_path(self):
        self.assertEqual(cd.get_project_dir({'name': 'owner/repo'}, '/out/dir'), '/out/dir/owner_repo')

    def test_get_project_dir_should_work_with_relative_path(self):
        self.assertEqual(cd.get_project_dir({'name': 'owner/repo'}, 'out/dir'), 'out/dir/owner_repo')

    def test_get_project_dir_should_work_with_ending_slash(self):
        self.assertEqual(cd.get_project_dir({'name': 'owner/repo'}, 'out/dir/'), 'out/dir/owner_repo')

    def test_get_project_dir_should_work_with_special_characters(self):
        self.assertEqual(cd.get_project_dir({'name': 'ow-ner/_r-e.p0'}, 'out/'), 'out/ow-ner__r-e.p0')

    def test_build_config_should_be_detected(self):
        for tool in TOOLS:
            project_dir = Path(__file__).parent / 'pass-all' / tool.command
            self.assertTrue(cd.has_tool(project_dir))

    def test_build_config_in_subdir_should_not_be_detected(self):
        parent_dir = Path(__file__).parent / 'pass-all'
        self.assertFalse(cd.has_tool(parent_dir))

    def test_excluded_technologies_should_be_excluded(self):
        projects = Path(__file__).parent / 'exclude'
        for project in projects.iterdir():
            self.assertTrue(cd.project_has_excluded_technology(project),
                            f"Exclusion failed for {project.name}")

    def test_included_technologies_should_not_be_excluded(self):
        projects = Path(__file__).parent / 'include'
        for project in projects.iterdir():
            self.assertFalse(cd.project_has_excluded_technology(project),
                             f"Inclusion failed for {project.name}")

    def test_file_should_match_present_patterns(self):
        file = Path(__file__).parent / 'match' / 'match.txt'
        patterns = [[r'match\.txt', r'start middle end'],
                    [r'.*\.txt', r'start middle .*'],
                    [r'match\..*', r'.* middle end'],]
        for name, content in patterns:
            self.assertTrue(cd.file_matches(file, name, content),
                            f"File {name} does not contain {content}")

    def test_file_should_not_match_absent_patterns(self):
        file = Path(__file__).parent / 'match' / 'match.txt'
        patterns = [[r'match', r'start middle end'],
                    [r'txt', r'start middle end'],
                    [r'.*', r'start middle'],
                    [r'.*', r'middle end']]
        for name, content in patterns:
            self.assertFalse(cd.file_matches(file, name, content),
                             f"File {name} contains {content}")

if __name__ == '__main__':
    main()
