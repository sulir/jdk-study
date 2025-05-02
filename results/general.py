import marimo

__generated_with = "0.13.4"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    from altair import Chart, Color, Scale, Text, Y
    from marimo import md, ui
    from pandas import DataFrame, read_csv
    from pandas.testing import assert_frame_equal
    from pathlib import Path
    from pymannkendall import original_test
    from sys import path
    path.insert(1, str(Path(globals()['__file__']).resolve().parent / '..'))
    from common import exit_notebook, require_path_args, RESULTS_CSV


@app.cell(hide_code=True)
def _():
    mo.md(r"""# General Results: RQ1 and H""")
    return


@app.cell
def _():
    results_dir, output_dir = require_path_args('results_dir', 'output_dir')
    results_csv = results_dir / RESULTS_CSV
    results_csv.is_file() or exit_notebook(f"File {results_csv} not found")
    output_dir.mkdir(parents=True, exist_ok=True)
    md(f"The notebook uses `{results_csv}` as input and `{output_dir}` for writing chart(s).")
    return output_dir, results_csv


@app.function
def get_results(results_csv):
    return read_csv(results_csv).set_index('name').sort_index()


@app.cell
def _(results_csv):
    results = get_results(results_csv)
    results
    return (results,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""This is the main data frame with build outcomes that will be necessary for multiple research questions:""")
    return


@app.function
def get_outcomes(results):
    outcomes = results.filter(regex='^java')
    outcomes.columns = outcomes.columns.str.removeprefix('java')
    exit_success = 0
    outcomes = outcomes == exit_success
    return outcomes


@app.cell
def _(results):
    outcomes = get_outcomes(results)
    outcomes
    return (outcomes,)


@app.function
def test_outcomes_reflect_exit_codes():
    sample_results = DataFrame({'name': ['p/1', 'p/2'], 'java6': [0, 1], 'java7': [1, 0]})
    sample_results.set_index('name', inplace=True)
    expected = DataFrame({'name': ['p/1', 'p/2'], '6': [True, False], '7': [False, True]})
    expected.set_index('name', inplace=True)
    assert_frame_equal(get_outcomes(sample_results), expected)


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## **RQ1:** What proportion of projects is buildable by their supplied script, using Java Development Kit versions ranging from 6 to 23?

    First, we create a summary table with success and failure rates (as percentages) for each Java version:
    """
    )
    return


@app.function
def get_rates(outcomes):
    return DataFrame({
        "Java version": outcomes.columns.map(int),
        "success": outcomes.mean() * 100,
        "failure": (1 - outcomes.mean()) * 100
    }).sort_values("Java version")


@app.cell
def _(outcomes):
    rates = get_rates(outcomes)
    rates
    return (rates,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""Next, we transform the outcomes to [long-form data](https://altair-viz.github.io/user_guide/data.html#long-form-vs-wide-form-data), which is a format that many visualization libraries expect.""")
    return


@app.cell
def _(rates):
    rates_long = rates.melt("Java version", ["failure", "success"], "Outcome", "Rate")
    rates_long
    return (rates_long,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""Finally, we plot the build success and failure rates as a stacked bar chart:""")
    return


@app.cell
def _(output_dir, rates_long):
    outcome_scale = Scale(
        domain=["failure", "success"],
        range=['#D2836F', '#4F9D69'])
    rates_bars = Chart(rates_long).mark_bar().encode(
        x="Java version:N",
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
def _():
    mo.md(
        r"""
    ## **H:** With increasing JDK version numbers, the proportion of build-failing projects tends to grow.

    We use the Mann-Kendall Test for monotonic trends.
    """
    )
    return


@app.function
def compute_trend(rates):
    mann_kendall = original_test(rates['failure'])
    return mann_kendall


@app.cell
def _(rates):
    h_result = compute_trend(rates)
    md(f"The p-value is **{h_result.p:.4f}**.\n\nThe type of the trend is: **{h_result.trend}**.")
    return


if __name__ == "__main__":
    app.run()
