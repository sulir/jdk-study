# Local Software Buildability across Java Versions

This repository contains scripts necessary to reproduce the results from the paper "Local Software Buildability across Java Versions", submitted to Empirical Software Engineering. The method was described in the ESEM 2024 [registered report](https://arxiv.org/pdf/2408.11544).

## Requirements

- Linux
- Python 3.10+
- Docker

Docker should be runnable without `sudo`. You can either configure the [rootless mode](https://docs.docker.com/engine/security/rootless/) or add the user to the ["docker" group](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user).

## Setup

First, change into the root directory of this project and create a Python virtual environment called `.venv`:

```bash
python -m venv .venv
```

Then activate it and install the required packages:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Study Replication

Before running the scripts, make sure you have the Python virtual environment activated (`source .venv/bin/activate`). Create an empty directory, e.g., `data` and place `github.csv` from the [data repository](https://doi.org/10.5281/zenodo.15232717) into it.

To execute the whole study, run the following command:

```bash
./jdk-study.sh data
```

This can take about two weeks though. To execute the study on a small sample of 3 projects, which should take under an hour, run:

```bash
./jdk-study.sh data 3
```

The following will be created in the `data` directory:
- `projects/`, `project.tar.xz`: The directory with the source code of the projects and its compressed version.
- `results.csv`: The main results file with build outcomes.
- `logs/`, `logs.tar.xz`: The directory with the build logs and its compressed version.
- `out/`: The output directory of Marimo notebooks with charts in the PDF format and a CSV file with error types.

At the end of the execution, four interactive [Marimo notebooks](https://marimo.io) will be open in the web browser.

## Notebooks

Static HTML versions of the Marimo notebooks can be generated using `results/generate-html.sh`. They are [available online for viewing](https://sulir.github.io/jdk-study/).

## Details

If more customization is needed, you can run the individual steps of the study:
- `dataset/create-dataset.py`: Creates a dataset of projects' source code from GitHub metadata.
- `dataset/split-dataset.py`: Splits the dataset into equal-sized parts to run the build processes in parallel on separate machines.
- `environment/build-images.py`: Builds Docker images for every Java version (no arguments necessary). The images are also available on [Docker Hub](https://hub.docker.com/r/sulir/jdk-study).
- `execution/run-builds.py`: Runs the build processes.
- `execution/join-results.py`: Joins the `results.csv` files and logs into one file/directory. The `results.csv` file and the projects' log directories (in the form `user_repo`) have to be together in each `source_dir`.
- `results/{general,projects,jdks,tools}.py`: Interactive Marimo notebooks that show the results of the hypothesis and research questions and generate charts. Run with `marimo edit <script> [args]`.
- `results/inspect-errors.py`: A helper script for the manual inspection of build logs.

For a list of arguments of a given script, execute it without arguments.

## Tests

Before running the tests, activate the Python virtual environment. To launch unit tests, run:

```bash
pytest
```

For running system tests (tens of minutes), execute:

```bash
pytest tests/sys*.py
```
