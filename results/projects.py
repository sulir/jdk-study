import marimo

__generated_with = "0.13.10"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    from pandas import read_csv
    from marimo import md, output, stop, ui
    from math import isclose
    from pathlib import Path
    from pty import spawn
    from sys import path
    path.insert(1, str(Path(globals()['__file__']).resolve().parent / '..'))
    from common import GITHUB_CSV, MAX_JAVA, RESULTS_CSV, exit_notebook, require_path_args
    from general import get_outcomes, get_results


@app.cell(hide_code=True)
def _():
    mo.md(r"""# Project-Related Questions""")
    return


@app.cell
def _():
    results_dir, output_dir = require_path_args('results_dir', 'output_dir')
    github_csv = results_dir / GITHUB_CSV
    github_csv.is_file() or exit_notebook(f"File {github_csv} not found")
    results_csv = results_dir / RESULTS_CSV
    results_csv.is_file() or exit_notebook(f"File {results_csv} not found")
    output_dir.mkdir(parents=True, exist_ok=True)
    md(f"The notebook uses `{github_csv}` and `{results_csv}` as inputs. The output directory is `{output_dir}`.")
    return github_csv, output_dir, results_csv, results_dir


@app.cell
def _(results_csv):
    results = get_results(results_csv)
    outcomes = get_outcomes(results)
    results.head(), outcomes.head()
    return outcomes, results


@app.cell(hide_code=True)
def _():
    mo.md(r"""## **RQ2:** What proportion of projects failing under the latest available JDK can be built using an earlier JDK?""")
    return


@app.cell(hide_code=True)
def _():
    mo.md(rf"""The latest JDK version in out study was {MAX_JAVA}.""")
    return


@app.function
def other_jdk_helps_percent(outcomes, current=MAX_JAVA):
    current_fail = outcomes[~outcomes[str(current)]]
    other_success = current_fail[current_fail.any(axis='columns')]
    return len(other_success) / len(current_fail) * 100


@app.cell
def _(outcomes):
    other_helps = other_jdk_helps_percent(outcomes)
    md(f"**{other_helps:.1f}%** of projects failing under the latest JDK can be built using an earlier JDK.")
    return


@app.cell(hide_code=True)
def _(outcomes):
    mo.md(rf"""If we consider the latest LTS version (21), another JDK helps {other_jdk_helps_percent(outcomes, 21):.1f}% of projects.""")
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## **RQ3:** What proportion of projects always fails, passes only for some JDKs, and passes for all JDKs?

    We divide the projects into three subsets based on the number of JDKs for which their build passed:
    """
    )
    return


@app.function
def passed_subsets(outcomes):
    versions = len(outcomes.columns)
    passed = outcomes.sum('columns')
    return {'none': outcomes[passed == 0],
            'part': outcomes[passed.between(1, versions - 1)],
            'all': outcomes[passed == versions]}


@app.cell
def _(outcomes):
    subsets = passed_subsets(outcomes)
    subsets
    return (subsets,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""Then we calculate the percentages of the total number of projects:""")
    return


@app.function
def passed_subsets_percent(subsets):
    total = sum(map(len, subsets.values()))
    return {k: 100 * len(v) / total for k, v in subsets.items()}


@app.cell
def _(subsets):
    subsets_percent = passed_subsets_percent(subsets)
    assert isclose(sum(subsets_percent.values()), 100)

    md(f"""**{subsets_percent['none']}%** of project always fail,
           **{subsets_percent['part']}%** pass only for some JDKs, and
           **{subsets_percent['all']}%** pass for all JDKs.
           {(subsets_percent['part'] + subsets_percent['all']):.1f}% pass for at least one JDK.""")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""For completeness, here are percentages of projects buildable with the given counts of JDKs:""")
    return


@app.cell
def _(outcomes):
    passed = outcomes.sum('columns')
    passed_jdk_counts_percent = passed.value_counts(normalize=True).mul(100).to_frame()
    passed_jdk_counts_percent.index.name = "version count"
    passed_jdk_counts_percent.columns.name = "percent"
    passed_jdk_counts_percent
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## **RQ4:** How do projects achieve compatibility with all JDKs at once?

    We load also the metadata from the [project search tool](https://seart-ghs.si.usi.ch), so they could be merged with our results for inspection:
    """
    )
    return


@app.cell
def _(github_csv):
    github = read_csv(github_csv).set_index('name')
    github.head()
    return (github,)


@app.cell(hide_code=True)
def _():
    trivial_lines = 1000
    md(f"This is a list of non-trivial projects (over {trivial_lines} non-blank source code lines) that are compatible with all JDK versions:")
    return (trivial_lines,)


@app.cell
def _(github, results, subsets, trivial_lines):
    compatible = results.loc[subsets['all'].index, ~results.columns.str.startswith('java')]
    compatible = compatible.join(github)
    compatible.drop(columns=['id', 'mainLanguage', 'metrics', 'labels', 'topics'], inplace=True)
    compatible = compatible[compatible['codeLines'] > trivial_lines]
    compatible
    return (compatible,)


@app.cell
def _(compatible, output_dir, results_dir):
    projects_tar = 'projects.tar.xz'
    compatible_dirs = ['projects/' + n.replace('/', '_') for n in compatible.index]
    extract_command = ['tar', 'xvf', results_dir / projects_tar, '-C', output_dir] + compatible_dirs
    extract_button = ui.run_button(label="Extract projects")
    output.append(md(f"To manually inspect these projects, place `{projects_tar}` into the results directory. " +
                     f"After clicking the button, they will be extracted to `{output_dir}`."))
    output.append(extract_button)
    return extract_button, extract_command


@app.cell
def _(extract_button, extract_command):
    stop(not extract_button.value)
    status = spawn(extract_command)
    md("Projects extracted.") if status == 0 else md("An error occurred.")
    return


if __name__ == "__main__":
    app.run()
