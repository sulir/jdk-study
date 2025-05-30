#!/usr/bin/env bash

tmp_dir=$(mktemp -d)
script_dir=$(dirname "$(realpath "$0")")
html_dir="html"
url=https://zenodo.org/records/15232718/files

for file in categories.csv github.csv logs.tar.xz results.csv; do
  curl -L -o "$tmp_dir/$file" "$url/$file?download=1"
done
tar xf "$tmp_dir/logs.tar.xz" -C "$tmp_dir"

for notebook in "$script_dir"/{general,projects,jdks,tools}.py; do
  marimo export html -o "$html_dir/$(basename "$notebook" .py).html" "$notebook" "$tmp_dir" "$tmp_dir/out"
done

rm -rf "$tmp_dir"
