from collections import namedtuple
from logging import INFO
from os import linesep
from pathlib import Path
from sys import argv, exit, stderr

LOG_CONFIG = {'level': INFO, 'format': '[%(asctime)s][%(levelname)s] %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
RANDOM_SEED = 4321

Tool = namedtuple('Tool', ['name', 'files', 'command', 'wrapper'])
TOOLS = [Tool('Gradle', ['build.gradle', 'build.gradle.kts',
                         'settings.gradle', 'settings.gradle.kts'], 'gradle', 'gradlew'),
         Tool('Maven', ['pom.xml'], 'mvn', 'mvnw'),
         Tool('Ant', ['build.xml'], 'ant', 'antw')]

MIN_JAVA = 6
MAX_JAVA = 23
IMAGE_NAME = 'sulir/jdk-study'
DOCKER_PROJECT_SRC = '/mnt/project'
GITHUB_CSV = 'github.csv'
RESULTS_CSV = 'results.csv'

def require_path_args(*args):
    if len(argv) == len(args) + 1:
        return map(Path, argv[1:])
    else:
        script_name = Path(argv[0]).name
        arg_names = ' '.join(f'<{a}>' for a in args)
        exit_notebook(f"Usage: marimo edit {script_name} {arg_names}")
        return []

def exit_notebook(message):
    print(message, file=stderr)
    from marimo import running_in_notebook, stop
    stop(True) if running_in_notebook() else exit(1)

def latex_table(data, highlight_max=False, rule_before_last=False):
    escaped = data.style.format_index(axis='columns', escape='latex')
    formatted = escaped.hide(axis='index').format(precision=1, escape='latex')
    if highlight_max:
        numeric_cols = data.select_dtypes(include='number').columns
        formatted = formatted.highlight_max(numeric_cols, axis='columns', props='textbf:--rwrap;')

    latex = formatted.to_latex(hrules=True, multicol_align='l')
    if rule_before_last:
        lines = latex.splitlines()
        lines.insert(lines.index(r'\bottomrule') - 1, r'\midrule')
        latex = linesep.join(lines) + linesep

    from marimo import ui
    return ui.code_editor(latex, language='stex', disabled=True)
