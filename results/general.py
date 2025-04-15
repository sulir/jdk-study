# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.0
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# ## Main hypothesis and RQ1

# %%
from pandas import read_csv
from pymannkendall import original_test
# %run ../common.py

# %% tags=["parameters"]
results_file = read_arg('results_file', "Enter path to results CSV file:")

# %%
results = read_csv(results_file)
results

# %%
def get_build_outcomes(results):
    outcomes = results.filter(regex='^java')
    outcomes.columns = outcomes.columns.str.removeprefix('java')
    return outcomes == 0

outcomes = get_build_outcomes(results)
outcomes

# %% [markdown]
# **RQ1:** What proportion of projects is buildable by their supplied script, using Java Development Kit versions ranging from 6 to 23?

# %%
success_rates = outcomes.mean()
print(success_rates.to_string())

# %% [markdown]
# **H:** With increasing JDK version numbers, the proportion of build-failing projects tends to grow.

# %%
mann_kendall = original_test(success_rates)
print(f"p-value: {mann_kendall.p}, trend: {mann_kendall.trend}")
