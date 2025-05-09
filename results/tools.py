import marimo

__generated_with = "0.13.6"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    from altair import Chart, Color, Scale, X, Y
    from marimo import md, ui
    from math import isclose
    from numpy import nan
    from pandas import concat, read_csv, DataFrame, MultiIndex
    from pathlib import Path
    from re import MULTILINE, findall, match, search
    from sys import path
    path.insert(1, str(Path(globals()['__file__']).resolve().parent / '..'))
    from common import MAX_JAVA, MIN_JAVA, RESULTS_CSV, exit_notebook, latex_table, require_path_args
    from general import get_results, get_outcomes


@app.cell(hide_code=True)
def _():
    mo.md(r"""# Tool-Related Questions""")
    return


@app.cell
def _():
    results_dir, output_dir = require_path_args('results_dir', 'output_dir')
    results_csv = results_dir / RESULTS_CSV
    results_csv.is_file() or exit_notebook(f"File {results_csv} not found")
    log_dir = results_dir / 'logs'
    log_dir.is_dir() or exit_notebook(f"Directory {log_dir} not found")
    categories_csv = results_dir / 'categories.csv'
    output_dir.mkdir(parents=True, exist_ok=True)
    md(f"The notebook uses `{results_csv}`, `{log_dir}`, and optionally `{categories_csv}` as input. " +
       f"For writing chart(s), `{output_dir}` is used.")
    return categories_csv, log_dir, output_dir, results_csv


@app.cell
def _(results_csv):
    results = get_results(results_csv)
    outcomes = get_outcomes(results)
    return outcomes, results


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## **RQ7:** What proportion of projects can be built using individual JDKs, per each build tool?

    We create a table with Gradle, Maven, and Ant as columns (grouped into a hierarchical index) and Java versions as rows. Values represent success rates as percentages. The last row contains the mean success rates of individual build tools for all Java versions together.
    """
    )
    return


@app.function
def get_tools(results, outcomes):
    tool_outcomes = results[["tool"]].join(outcomes)
    tools = tool_outcomes.groupby("tool").mean().transpose() * 100

    tool_order = ["Gradle", "Maven", "Ant"]
    tools = tools[tool_order]
    tools.columns = MultiIndex.from_product([["Success rate (%)"], tool_order])
    tools.insert(0, ("", "Java version"), tools.index)

    means = tools.iloc[:, 1:].mean()
    tools.loc["Mean"] = ["Mean"] + means.tolist()
    return tools


@app.cell
def _(outcomes, results):
    tools = get_tools(results, outcomes)
    tools
    return (tools,)


@app.cell
def _(tools):
    latex_table(tools)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""A long-format version of the table is created and the data is visualized using a line plot.""")
    return


@app.cell
def _(tools):
    tools_no_mean = tools[tools.iloc[:, 0].map(lambda v: v.isnumeric())]
    tools_long = tools_no_mean.melt("Java version", var_name="Tool", value_name="success", col_level=1)
    tools_long["Java version"] = tools_long["Java version"].astype(int)
    tools_long
    return (tools_long,)


@app.cell
def _(output_dir, tools_long):
    tool_colors = Scale(
        domain=["Gradle", "Maven", "Ant"],
        range=['#009E73', '#104E8B', '#CC79A7']
    )
    tools_plot = Chart(tools_long).mark_line(point=True).encode(
        x=X("Java version", scale=Scale(domain=[MIN_JAVA, MAX_JAVA])),
        y=Y("success", title="Success rate (%)"),
        color=Color("Tool", sort=None, scale=tool_colors)
    ).properties(width=600, height=300)

    tools_plot.save(output_dir / 'tools.pdf')
    ui.altair_chart(tools_plot)
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## **RQ8:** Are there differences in failure rates between the projects utilizing wrappers and the projects requiring system-wide build tool installation?

    We create a table similar to RQ7, now with each build tool divided a non-wrapper (system) and wrapper version. No project in our dataset uses the Ant wrapper (antw), so we will exclude Ant from this analysis.
    """
    )
    return


@app.function
def get_wrappers(results, outcomes):
    wrapper_data = results.loc[results["tool"] != "Ant", ["tool", "wrapper"]]
    wrapper_outcomes = wrapper_data.join(outcomes)
    wrapper_outcomes.replace({"gradlew": "wrapper", "mvnw": "wrapper", nan: "system"}, inplace=True)
    percent = wrapper_outcomes.groupby(["tool", "wrapper"]).mean().transpose() * 100
    percent.insert(0, ("", "Java version"), percent.index)

    means = percent.iloc[:, 1:].mean()
    percent.loc["Mean"] = ["Mean"] + means.tolist()
    return percent


@app.cell
def _(outcomes, results):
    wrappers = get_wrappers(results, outcomes)
    wrappers
    return (wrappers,)


@app.cell
def _(wrappers):
    latex_table(wrappers)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""## **RQ9:** What are the most common build failure reasons?""")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""First, we create a long-form table of all failed builds:""")
    return


@app.function
def get_failed(results):
    exit_codes = results.drop(["commit", "wrapper"], axis='columns')
    results_long = exit_codes.melt("tool", ignore_index=False, var_name="jdk", value_name="status")
    failed = results_long[results_long["status"] != 0].copy()
    failed["jdk"] = failed["jdk"].str.removeprefix('java').astype(int)
    failed = failed.sort_values(["name", "jdk"])
    return failed.reset_index()


@app.cell
def _(results):
    failed = get_failed(results)
    failed
    return (failed,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""Next, the log of every failed build is analyzed using build-tool-specific logic (unless an exit code signifies a timeout or a Java Virtual Machine crash). An error type is assigned to each such build.""")
    return


@app.function
def get_failed_types(projects, log_dir):
    extractors = {"Gradle": gradle_error, "Maven": maven_error, "Ant": ant_error}
    error_types = []

    for project in projects.itertuples():
        if project.status == 124:
            error_type = 'Timeout'
        elif project.status == 134:
            error_type = 'Crash'
        else:
            file = log_dir / project.name.replace('/', '_') / f'{project.jdk:02d}.fail'
            log_content = file.read_text()
            error_type = extractors[project.tool](log_content)
        error_types.append(error_type)

    projects = projects.assign(type=error_types)
    return projects.drop("status", axis='columns')


@app.cell(hide_code=True)
def _():
    mo.md(r"""For Gradle, we use a special error type "Resolve" if a string representing dependency resolution failure is present. Otherwise, we return the name of failed task, including the colon. If no task was marked as failed by Gradle, it means an error occurred during the initialization of a project or a subproject, so we use the "Init" error type.""")
    return


@app.function
def gradle_error(log):
    lines = log.splitlines()
    last_task = None

    for line in lines:
        if line.startswith('> Could not resolve '):
            return 'Resolve'

        task = match(r'(> Task )?(:[\w.-]+)+', line)
        if task:
            last_task = task.group(2)
        if last_task and line.endswith(' FAILED'):
            return last_task

    return 'Init'


@app.cell(hide_code=True)
def _():
    mo.md(r"""For Maven, we use the "Init" error type if the initial information message about building the project is not present in the log. If the build ended with a `DependencyResolutionException` or `PluginResolutionException` and it contains a help link describing this error, a special error type "Resolve" is returned. Otherwise, we search the log a for a Maven plugin name that caused the failure and use it as an error type. If none of the previously mentioned patterns were found, we return "Other".""")
    return


@app.function
def maven_error(log):
    if '[INFO] Building' not in log:
        return 'Init'

    resolve = r'^\[ERROR] \[Help \d] http://.*/(Dependency|Plugin)ResolutionException$'
    if search(resolve, log, MULTILINE):
        return 'Resolve'

    execute = "Failed to execute goal"
    find = "Could not find goal '.+?' in plugin"
    plugin = search(fr'^\[ERROR] ({execute}|{find}) .+?:(.+?):', log, MULTILINE)
    if plugin:
        return plugin.group(2)

    return 'Other'


@app.cell(hide_code=True)
def _():
    mo.md(r"""Ant logs consist of multiple sequentially executed processes. We ignore the first `clean` target process and then find the first process that did not fail because of an invalid target name (e.g., `jar`). If no such process exists, we analyze the last one. In the analyzed log, we return the name of the last executed target, or "Init" if no target was yet executed.""")
    return


@app.function
def ant_error(log):
    before = r'(?:Picked up .+\n)?Buildfile: /.+\n'
    after = r'\nTotal time: .+ seconds?\n'
    exclude_clean = 1
    processes = findall(fr'{before}([\s\S]*?){after}', log)[exclude_clean:]

    bad_target = r'BUILD FAILED\nTarget "(jar|war|dist)" does not exist in the project'
    valid_targets = list(p for p in processes if not search(bad_target, p))
    analyzed = valid_targets[0] if valid_targets else processes[-1]

    targets = findall(r'^([\w.-]+):$', analyzed, MULTILINE)
    if targets:
        return 'ant:' + targets[-1]
    else:
        return 'Init'


@app.cell(hide_code=True)
def _():
    mo.md(r"""Here is a table with all builds having an error type assigned:""")
    return


@app.cell
def _(failed, log_dir):
    failed_types = get_failed_types(failed, log_dir)
    failed_types
    return (failed_types,)


@app.cell(hide_code=True)
def _(error_counts):
    mo.md(rf"""The following table shows a list of all {len(error_counts)} unique error types, sorted from the most to the least frequent ones. The last column represents cumulative percentages of builds. This is useful to select the subset of error types for the manual assignment of categories. For example, to have at least 98% of builds categorized, we need to manually categorize {error_counts.index[error_counts['sum_percent'] >= 98][0] + 1} error types.""")
    return


@app.function
def get_error_counts(failed_types):
    counts = failed_types.type.value_counts().reset_index()
    total = counts["count"].sum()
    counts["sum_percent"] = counts["count"].cumsum() / total * 100
    return counts


@app.cell
def _(failed_types):
    error_counts = get_error_counts(failed_types)
    error_counts
    return (error_counts,)


@app.cell(hide_code=True)
def _(categories_csv):
    mo.md(rf"""The file `{categories_csv}` is supposed to be created manually by the researchers. It maps each machine-readable error type (from the tables above) to one human-readable error category. It should contain columns `type` and `category`. If it does not yet exist, we use a "demo" file that only maps `maven-compiler-plugin` type to the "compilation" category. Error types not present in the file are assigned to the "other/unknown" category by default.""")
    return


@app.cell
def _(categories_csv):
    def get_categories():
        if categories_csv.is_file():
            return read_csv(categories_csv)
        else:
            return DataFrame([['maven-compiler-plugin', "compilation"]], columns=["type", "category"])
    return (get_categories,)


@app.cell
def _(get_categories):
    categories = get_categories()
    categories
    return (categories,)


@app.cell(hide_code=True)
def _():
    mo.md(rf"""Finally, we present the table of percentages of failure categories for every Java version. Totals for all Java versions are also computed. The LaTeX table has maximums of each row highlighted in bold.""")
    return


@app.function
def get_categories_percent(failed_types, categories):
    default = "other/unknown"
    categorized = failed_types.merge(categories, 'left', "type").fillna(default)
    categorized = categorized[["jdk", "category"]]
    proportions = categorized.groupby("jdk").value_counts(normalize=True)
    percentages = proportions.mul(100).rename("percent").reset_index()
    wide = percentages.pivot(columns="category", index="jdk", values="percent").fillna(0)

    order = ["initialization", "dependency resolution", "resource processing", "compilation",
             "documentation", "extra plugins", "packaging", "timeout", default]
    order = [c for c in order if c in wide.columns]
    wide = wide.reindex(columns=order)

    total = categorized["category"].value_counts(normalize=True)
    total = total.mul(100).rename("Total").to_frame()
    total = total.transpose().reindex(columns=order)
    total.index = ["Total"]

    result = concat([wide, total])
    result.index.name = "Java version"
    result.columns = MultiIndex.from_product([["Failure category (%)"], result.columns])
    return result.reset_index()


@app.cell
def _(categories, failed_types):
    categories_percent = get_categories_percent(failed_types, categories)
    assert categories_percent.sum(axis=1, numeric_only=True).map(lambda s: isclose(s, 100)).all()
    categories_percent
    return (categories_percent,)


@app.cell
def _(categories_percent):
    latex_table(categories_percent, highlight_max=True)
    return


if __name__ == "__main__":
    app.run()
