

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# General Results: RQ1 and H""")
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from altair import Chart, Color, Scale, Text, X, Y
    from marimo import md, running_in_notebook, stop, ui
    from pandas import DataFrame, read_csv
    from pandas.testing import assert_frame_equal
    from pathlib import Path
    from pymannkendall import original_test
    from sys import argv, exit, stderr
    from helpers import RESULTS_CSV
    return (
        Chart,
        Color,
        DataFrame,
        Path,
        RESULTS_CSV,
        Scale,
        Text,
        X,
        Y,
        argv,
        assert_frame_equal,
        exit,
        md,
        mo,
        original_test,
        read_csv,
        running_in_notebook,
        stderr,
        stop,
        ui,
    )


@app.cell(hide_code=True)
def _(RESULTS_CSV, md):
    md(f"The notebook requires `{RESULTS_CSV}` and an output directory for writing chart(s).")
    return


@app.cell
def _(
    Path,
    RESULTS_CSV,
    __file__,
    argv,
    exit,
    running_in_notebook,
    stderr,
    stop,
):
    if len(argv) == 3:
        results_dir = Path(argv[1])
        results_csv = results_dir / RESULTS_CSV
        output_dir = Path(argv[2])
    else:
        print(f"Usage: [python|marimo edit] {Path(__file__).name} results_dir output_dir", file=stderr)
        stop(True) if running_in_notebook() else exit(1)
    return output_dir, results_csv


@app.cell
def _(read_csv, results_csv):
    results = read_csv(results_csv).sort_values('name')
    results
    return (results,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""This is the main data frame with build outcomes that will be necessary for multiple research questions:""")
    return


@app.cell
def _(results):
    def get_build_outcomes(results):
        outcomes = results.filter(regex='^java')
        outcomes.columns = outcomes.columns.str.removeprefix('java')
        outcomes = outcomes == 0
        outcomes.insert(0, 'name', results['name'])
        return outcomes

    outcomes = get_build_outcomes(results)
    outcomes
    return get_build_outcomes, outcomes


@app.cell
def _(DataFrame, assert_frame_equal, get_build_outcomes):
    def test_build_outcomes():
        sample_results = DataFrame({'name': ['p/1', 'p/2'], 'java6': [0, 1], 'java7': [1, 0]})
        expected = DataFrame({'name': ['p/1', 'p/2'], '6': [True, False], '7': [False, True]})
        assert_frame_equal(get_build_outcomes(sample_results), expected)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## **RQ1:** What proportion of projects is buildable by their supplied script, using Java Development Kit versions ranging from 6 to 23?

        First, we create a summary table with success and failure rates (as percentages) for each Java version:
        """
    )
    return


@app.cell
def _(DataFrame, outcomes):
    outcome_values = outcomes.drop('name', axis='columns')
    rates = DataFrame({
        "Java version": outcome_values.columns.map(int),
        "success": outcome_values.mean(),
        "failure": 1 - outcome_values.mean()
    }).sort_values("Java version")
    rates[["success", "failure"]] *= 100
    rates
    return (rates,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Next, we transform the outcomes to [long-form data](https://altair-viz.github.io/user_guide/data.html#long-form-vs-wide-form-data), which is a format that many visualization libraries expect.""")
    return


@app.cell
def _(rates):
    rates_long = rates.melt("Java version", ["failure", "success"], "Outcome", "Rate")
    rates_long
    return (rates_long,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Finally, we plot the build success and failure rates as a stacked bar chart:""")
    return


@app.cell
def _(Chart, Color, Scale, Text, X, Y, output_dir, rates_long, ui):
    outcome_scale = Scale(
        domain=["failure", "success"],
        range=['#D2836F', '#4F9D69'])
    rates_bars = Chart(rates_long).mark_bar().encode(
        x=X("Java version:N"),
        y=Y("Rate", title="Projects (%)", scale=Scale(domain=[0, 100])),
        color=Color("Outcome", scale=outcome_scale)
    ).properties(width=600, height=200)

    def make_labels(outcome, compute_pos):
        labels = rates_long.query("Outcome == @outcome").copy()
        labels['pos'] = labels["Rate"].apply(compute_pos)
        return Chart(labels).mark_text(color='white').encode(
            x="Java version:N",
            text=Text("Rate", format='.1f'),
            y='pos')

    success_labels = make_labels("success", lambda r: max(4, r - 4))
    failure_labels = make_labels("failure", lambda _: 96)
    rates_chart = rates_bars + success_labels + failure_labels
    rates_chart.save(output_dir / 'rates.pdf')
    ui.altair_chart(rates_chart)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## **H:** With increasing JDK version numbers, the proportion of build-failing projects tends to grow.

        We use the Mann-Kendall Test for monotonic trends.
        """
    )
    return


@app.cell
def _(md, original_test, rates):
    mann_kendall = original_test(rates['success'])
    md(f"The p-value is **{mann_kendall.p:.4f}**.\n\nThe type of the trend is: **{mann_kendall.trend}**.")
    return


if __name__ == "__main__":
    app.run()
