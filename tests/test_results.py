from pandas import DataFrame
from pandas.testing import assert_frame_equal
from pathlib import Path
from sys import path
from unittest import TestCase, main
path.insert(1, str((Path(__file__).parent / '..' / 'results').resolve()))
from results.general import get_outcomes, get_rates

class TestResults(TestCase):
    def test_outcomes_reflect_exit_codes(self):
        results = DataFrame({'name': ['p/1', 'p/2'], 'java6': [0, 1], 'java7': [1, 0]})
        results.set_index('name', inplace=True)
        expected = DataFrame({'name': ['p/1', 'p/2'], '6': [True, False], '7': [False, True]})
        expected.set_index('name', inplace=True)
        assert_frame_equal(get_outcomes(results), expected)

    def test_rates_reflect_outcomes(self):
        outcomes = DataFrame({'name': ['p/1', 'p/2'],
                              '6': [False, False], '7': [True, False], '8': [True, True]})
        outcomes.set_index('name', inplace=True)
        expected = DataFrame({'Java version': [6, 7, 8],
                              'success': [0.0, 50.0, 100.0],
                              'failure': [100.0, 50.0, 0.0]})
        result = get_rates(outcomes)
        result.reset_index(drop=True, inplace=True)
        assert_frame_equal(result, expected)

if __name__ == '__main__':
    main()
