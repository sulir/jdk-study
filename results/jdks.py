import marimo

__generated_with = "0.13.6"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    from altair import Axis, Chart, Color, Scale, X, Y, datum, expr
    from marimo import hstack, md, output, plain, ui
    from pandas import option_context
    from pathlib import Path
    from sys import path
    path.insert(1, str(Path(globals()['__file__']).resolve().parent / '..'))
    from common import MAX_JAVA, MIN_JAVA, RESULTS_CSV, exit_notebook, latex_table, require_path_args
    from general import get_outcomes, get_rates, get_results


@app.cell(hide_code=True)
def _():
    mo.md(r"""# JDK-related questions""")
    return


@app.cell
def _():
    results_dir, output_dir = require_path_args('results_dir', 'output_dir')
    results_csv = results_dir / RESULTS_CSV
    results_csv.is_file() or exit_notebook(f"File {results_csv} not found")
    output_dir.mkdir(parents=True, exist_ok=True)
    md(f"The notebook uses `{results_csv}` for input and `{output_dir}` as an output directory.")
    return output_dir, results_csv


@app.cell(hide_code=True)
def _():
    mo.md(r"""We load the build outcomes for all projects and success rates of JDKs:""")
    return


@app.cell
def _(results_csv):
    results = get_results(results_csv)
    outcomes = get_outcomes(results)
    rates = get_rates(outcomes)
    return outcomes, rates


@app.cell(hide_code=True)
def _():
    mo.md(r"""## **RQ5:** Which JDK version can build the largest/smallest number of projects?""")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""We sort the Java versions from the most to least successful:""")
    return


@app.cell
def _(rates):
    jdk_rates = rates.sort_values("success", ascending=False)
    jdk_rates.drop("failure", axis='columns', inplace=True)
    jdk_rates.rename(columns={"success": "Success rate (%)"}, inplace=True)
    jdk_latex = latex_table(jdk_rates)

    with option_context('display.max_rows', None):
        widgets = [plain(jdk_rates), jdk_latex]
        output.append(hstack(widgets, justify='start'))
    return (jdk_rates,)


@app.cell
def _(jdk_rates):
    best_jdk, best_rate = jdk_rates.iloc[0]
    worst_jdk, worst_rate = jdk_rates.iloc[-1]
    md(f"The largest number of projects, {best_rate}%, can be built with **JDK {best_jdk}**. " +
       f"The most failing version, **JDK {worst_jdk}**, builds only {worst_rate}% of projects.")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""## **RQ6:** Which JDK versions cause sudden drops in the passing rate?""")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""For each JDK version, we calculate the difference between its success rate and the success rate of the previous version in percentage points.""")
    return


@app.function
def get_jdk_changes(rates):
    changes = rates.drop("failure", axis='columns')
    changes.insert(1, "previous", changes["success"].shift())
    changes["difference"] = changes["success"].diff()
    changes["change"] = changes["difference"].map(lambda c: f'{c:+.1f}').replace('+nan', '')
    changes["direction"] = changes["change"].str[0].replace({'-': "decrease", '+': "increase"})
    return changes


@app.cell
def _(rates):
    jdk_changes = get_jdk_changes(rates)
    jdk_changes
    return (jdk_changes,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""The following chart is a combination of a line plot of success rates of JDK versions and a candlestick plot (without shadows) of differences from the previous version. LTS (long-term support) versions are bold on the x-axis.""")
    return


@app.cell
def _(jdk_changes, output_dir):
    x_scale = Scale(domain=[MIN_JAVA, MAX_JAVA], padding=15)
    lts_versions = [8, 11, 17, 21]
    bold_lts = expr(expr.if_(expr.indexof(lts_versions, datum.value) != -1, 'bold', 'normal'))

    line_plot = Chart(jdk_changes).mark_line(color='#6488EA', opacity=0.5, point=True).encode(
        x=X("Java version", scale=x_scale, axis=Axis(labelFontWeight=bold_lts)),
        y=Y("success", title="Success rate (%)")
    )
    candlesticks = Chart(jdk_changes).mark_bar(size=4).encode(
        x=X("Java version", scale=x_scale),
        y="previous",
        y2="success",
        color=Color("direction", scale=Scale(
            domain=["decrease", "increase"],
            range=['#D2836F', '#4F9D69']
        ), title="Change type")
    )
    labels = Chart(jdk_changes).mark_text(
        dy=expr(expr.if_(datum.direction == "decrease", 10, -10))
    ).encode(
        x=X("Java version", scale=x_scale),
        y="success",
        text="change",
    )

    changes_chart = (candlesticks + line_plot + labels).properties(width=600, height=300)
    changes_chart.save(output_dir / 'changes.pdf')
    ui.altair_chart(changes_chart)
    return


@app.cell
def _(jdk_changes):
    jdk_drops = jdk_changes.sort_values("difference").head(3)
    report_format = lambda r: f"JDK **{r['Java version']}** ({r['change']} pp)"
    jdk_drops_str = ", ".join(jdk_drops.apply(report_format, axis='columns'))
    md(f"Java version having the largest drop in the passing rate are: {jdk_drops_str}.")
    return (jdk_drops,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""For each of these versions, we also provide a list of projects that are passing with the previous JDK but failing for all subsequent versions. It can be useful for the manual inspection of breaking changes in JDKs using the logs.""")
    return


@app.cell
def _(jdk_drops, outcomes):
    jdk_pairs = [(str(v - 1), str(v)) for v in jdk_drops["Java version"]]
    for passed, failed in jdk_pairs:
        fail_from = outcomes.columns.get_loc(failed)
        projects = outcomes[outcomes[passed] & ~outcomes.iloc[:, fail_from:].any(axis='columns')]
        output.append(md(f"Projects passing with JDK {passed} and failing from JDK {failed} onward:"))
        output.append(list(projects.index))
    return


if __name__ == "__main__":
    app.run()
