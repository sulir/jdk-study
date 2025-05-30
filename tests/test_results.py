from pandas import DataFrame
from pandas.testing import assert_frame_equal
from pathlib import Path
from sys import path
from unittest import TestCase, main
path.insert(1, str((Path(__file__).parent / '..' / 'results').resolve()))
from results.general import get_outcomes

class TestResults(TestCase):
    def test_outcomes_reflect_exit_codes(self):
        sample_results = DataFrame({'name': ['p/1', 'p/2'], 'java6': [0, 1], 'java7': [1, 0]})
        sample_results.set_index('name', inplace=True)
        expected = DataFrame({'name': ['p/1', 'p/2'], '6': [True, False], '7': [False, True]})
        expected.set_index('name', inplace=True)
        assert_frame_equal(get_outcomes(sample_results), expected)

if __name__ == '__main__':
    main()
