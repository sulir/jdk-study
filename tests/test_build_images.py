from pathlib import Path
from sys import path
from unittest import main, TestCase
path.insert(1, str((Path(__file__).parent / '..' / 'environment').resolve()))
bi = __import__('build-images')

class TestBuildImages(TestCase):
    def test_zulu_jdk_version_matches_major_java_version(self):
        for java_version in range(bi.MIN_JAVA, bi.MAX_JAVA + 1):
            with self.subTest(java_version=java_version):
                zulu_version = bi.get_version('Zulu', java_version)
                jdk_version = bi.get_version('JDK', java_version)
                self.assertEqual(zulu_version.split('.')[0], str(java_version))
                self.assertEqual(jdk_version.split('.')[0], str(java_version))

    def test_bouncy_castle_is_only_for_java_6(self):
        for java_version in range(bi.MIN_JAVA, bi.MAX_JAVA + 1):
            with self.subTest(java_version=java_version):
                bc_version = bi.get_version('Bouncy_Castle', java_version)
                if java_version == 6:
                    self.assertNotEqual(bc_version, '')
                else:
                    self.assertEqual(bc_version, '')

if __name__ == '__main__':
    main()
