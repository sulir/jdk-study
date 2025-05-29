#!/usr/bin/env bash

DEFAULT_COUNT=2500

case "$#" in
  1)
    project_count=$DEFAULT_COUNT ;;
  2)
    project_count=$2 ;;
  *)
    echo "Usage: $0 <data_dir> <project_count>"
    exit 1
esac

data_dir=$1
script_dir=$(dirname "$(realpath "$0")")

[ -d "$data_dir" ] || { echo "Directory $data_dir should exist"; exit 1; }
[ "$(ls "$data_dir")" = "github.csv" ] || { echo "$data_dir should contain exactly one file: github.csv"; exit 1; }

"$script_dir/dataset/create-dataset.py" "$data_dir/github.csv" "$data_dir/projects" "$project_count" || exit 1
tar cJf "$data_dir/projects.tar.xz" -C "$data_dir" projects

"$script_dir/environment/build-images.py" || exit 1

"$script_dir/execution/run-builds.py" "$data_dir/projects" "$data_dir" "$data_dir/logs" || exit 1
tar cJf "$data_dir/logs.tar.xz" -C "$data_dir" logs

for notebook in "$script_dir"/results/{general,projects,jdks,tools}.py; do
  marimo edit "$notebook" "$data_dir" "$data_dir/out" &
  sleep 2
done
