import sys
from pathlib import Path
from shutil import rmtree
from subprocess import DEVNULL, run
from tempfile import mkdtemp
from unittest import TestCase, main

sys.path.insert(1, str(Path(__file__).resolve().parent / ".."))
sys.path.insert(1, str(Path(__file__).resolve().parent / ".." / "results"))
from common import MAX_JAVA, MIN_JAVA, RESULTS_CSV
from results import general, jdks, projects, tools

# Java versions range
NUM_JAVA_VERSIONS = MAX_JAVA - MIN_JAVA + 1
JAVA_VERSIONS = list(range(MIN_JAVA, MAX_JAVA + 1))

# Number of passed builds for each Java version
ANT_PASS = [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
GRADLE_WRAPPER_PASS = [0, 1, 0] + [0] * (NUM_JAVA_VERSIONS - 3)
GRADLE_SYSTEM_PASS = [2, 1, 1] + [1] * (NUM_JAVA_VERSIONS - 3)
GRADLE_PASS = [s + w for s, w in zip(GRADLE_SYSTEM_PASS, GRADLE_WRAPPER_PASS)]
MAVEN_SYSTEM_PASS = [2, 1, 1] + [1] * (NUM_JAVA_VERSIONS - 3)
MAVEN_WRAPPER_PASS = [0, 1, 1] + [0] * (NUM_JAVA_VERSIONS - 3)
MAVEN_PASS = [s + w for s, w in zip(MAVEN_SYSTEM_PASS, MAVEN_WRAPPER_PASS)]
ALL_PASS = [a + g + m for a, g, m in zip(ANT_PASS, GRADLE_PASS, MAVEN_PASS)]

# Differences in success rates between Java versions
DIFFERENCES = [0, -2, -1] + [0] * (NUM_JAVA_VERSIONS - 4)

# Number of projects
ANT_PROJECTS = 4
GRADLE_WRAPPER_PROJECTS = 1
GRADLE_SYSTEM_PROJECTS = 3
GRADLE_PROJECTS = GRADLE_WRAPPER_PROJECTS + GRADLE_SYSTEM_PROJECTS
MAVEN_WRAPPER_PROJECTS = 1
MAVEN_SYSTEM_PROJECTS = 3
MAVEN_PROJECTS = MAVEN_WRAPPER_PROJECTS + MAVEN_SYSTEM_PROJECTS
ALL_PROJECTS = ANT_PROJECTS + GRADLE_PROJECTS + MAVEN_PROJECTS

# Number of projects with different outcomes
ALWAYS_FAIL = 3
ALWAYS_PASS = 3
PARTIALLY_PASS = 6
EARLIER_JDK_HELPS_PERCENT = 66.666666667


class TestResults(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.create_images()
        cls.DATASET_DIR = Path(__file__).parent / "sample-projects"
        cls.RESULTS_DIR = mkdtemp()
        print("Using results directory:", cls.RESULTS_DIR)
        cls.run_builds()

    @classmethod
    def create_images(cls):
        build_images = (
            Path(__file__).parent / ".." / "environment" / "build-images.py"
        ).resolve()
        run([sys.executable, build_images], stdout=DEVNULL, stderr=DEVNULL, check=True)

    @classmethod
    def run_builds(cls):
        run_build = (
            Path(__file__).parent / ".." / "execution" / "run-builds.py"
        ).resolve()
        run([sys.executable, run_build, cls.DATASET_DIR, cls.RESULTS_DIR], check=True)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.RESULTS_DIR)

    def setUp(self):
        results_csv = Path(self.RESULTS_DIR) / RESULTS_CSV
        self.results = general.get_results(results_csv)
        self.outcomes = general.get_outcomes(self.results)

    def test_h(self):
        rates = general.get_rates(self.outcomes)
        result = general.compute_trend(rates)

        self.assertEqual(result.trend, "increasing")
        self.assertAlmostEqual(result.p, 0.0066849)

    def test_rq1(self):
        rates = general.get_rates(self.outcomes)

        self.assertEqual(rates.columns.tolist(), ["Java version", "success", "failure"])

        self.assertEqual(
            rates["Java version"].tolist(),
            JAVA_VERSIONS,
        )
        self.assertAllAlmostEqual(
            rates["success"].tolist(),
            [r / ALL_PROJECTS * 100 for r in ALL_PASS],
        )
        self.assertAllAlmostEqual(
            rates["failure"].tolist(),
            [(1 - r / ALL_PROJECTS) * 100 for r in ALL_PASS],
        )

    def test_rq2(self):
        earlier_helps = projects.earlier_jdk_helps_percent(self.outcomes)

        self.assertAlmostEqual(earlier_helps, EARLIER_JDK_HELPS_PERCENT)

    def test_rq3(self):
        subsets = projects.passed_subsets(self.outcomes)
        subsets_percent = projects.passed_subsets_percent(subsets)
        self.assertAlmostEqual(
            subsets_percent["none"], ALWAYS_FAIL / ALL_PROJECTS * 100
        )
        self.assertAlmostEqual(
            subsets_percent["part"], PARTIALLY_PASS / ALL_PROJECTS * 100
        )
        self.assertAlmostEqual(subsets_percent["all"], ALWAYS_PASS / ALL_PROJECTS * 100)

    def test_rq6(self):
        rates = general.get_rates(self.outcomes)
        jdk_changes = jdks.get_jdk_changes(rates)
        self.assertAllAlmostEqual(
            jdk_changes["difference"][1:].tolist(),
            [d / ALL_PROJECTS * 100 for d in DIFFERENCES],
        )

    def test_rq7(self):
        tools_rates = tools.get_tools(self.results, self.outcomes)

        self.assertEqual(
            tools_rates.columns.tolist(),
            [
                ("", "Java version"),
                ("Success rate (%)", "Gradle"),
                ("Success rate (%)", "Maven"),
                ("Success rate (%)", "Ant"),
            ],
        )
        self.assertEqual(
            tools_rates[("", "Java version")].tolist(),
            [str(i) for i in JAVA_VERSIONS] + ["Mean"],
        )

        self.assertAllAlmostEqual(
            tools_rates[("Success rate (%)", "Gradle")].tolist(),
            with_mean([r / GRADLE_PROJECTS * 100 for r in GRADLE_PASS]),
        )

        self.assertAllAlmostEqual(
            tools_rates[("Success rate (%)", "Maven")].tolist(),
            with_mean([r / MAVEN_PROJECTS * 100 for r in MAVEN_PASS]),
        )

        self.assertAllAlmostEqual(
            tools_rates[("Success rate (%)", "Ant")].tolist(),
            with_mean([r / ANT_PROJECTS * 100 for r in ANT_PASS]),
        )

    def test_rq8(self):
        wrappers = tools.get_wrappers(self.results, self.outcomes)
        self.assertEqual(
            wrappers.columns.tolist(),
            [
                ("", "Java version"),
                ("Gradle", "system"),
                ("Gradle", "wrapper"),
                ("Maven", "system"),
                ("Maven", "wrapper"),
            ],
        )
        self.assertEqual(
            wrappers[("", "Java version")].tolist(),
            [str(i) for i in JAVA_VERSIONS] + ["Mean"],
        )
        self.assertAllAlmostEqual(
            wrappers[("Gradle", "system")].tolist(),
            with_mean([r / GRADLE_SYSTEM_PROJECTS * 100 for r in GRADLE_SYSTEM_PASS]),
        )
        self.assertAllAlmostEqual(
            wrappers[("Gradle", "wrapper")].tolist(),
            with_mean([r / GRADLE_WRAPPER_PROJECTS * 100 for r in GRADLE_WRAPPER_PASS]),
        )

        self.assertAllAlmostEqual(
            wrappers[("Maven", "system")].tolist(),
            with_mean([r / GRADLE_SYSTEM_PROJECTS * 100 for r in MAVEN_SYSTEM_PASS]),
        )
        self.assertAllAlmostEqual(
            wrappers[("Maven", "wrapper")].tolist(),
            with_mean([r / MAVEN_WRAPPER_PROJECTS * 100 for r in MAVEN_WRAPPER_PASS]),
        )

    def assertAllAlmostEqual(self, actual, expected):
        for i in range(len(actual)):
            self.assertAlmostEqual(
                actual[i],
                expected[i],
                msg=f"Failed at index {i}: {actual[i]} != {expected[i]}",
            )


def with_mean(expected):
    return expected + [sum(expected) / len(expected)]


if __name__ == "__main__":
    main()
