#!/usr/bin/env python3
from csv import DictReader
from pathlib import Path
from random import sample
from subprocess import run
from sys import argv

SAMPLE_SIZE = 3
EDITOR = 'xdg-open'

def main(error_types_csv, log_dir):
    rows_by_type = {}
    with error_types_csv.open() as file:
        for row in DictReader(file):
            rows_by_type.setdefault(row['type'], []).append(row)

    while error_type := input("Error type (empty=quit): "):
        if error_type not in rows_by_type:
            print("Error type not found.")
            continue
        rows = rows_by_type[error_type]
        examples = sample(rows, min(SAMPLE_SIZE, len(rows)))
        for row in examples:
            dir_name = row['name'].replace('/', '_')
            log_path = log_dir / dir_name / f"{int(row['jdk']):02d}.fail"
            run([EDITOR, log_path])

if __name__ == '__main__':
    if len(argv) == 3:
        main(Path(argv[1]), Path(argv[2]))
    else:
        print("Usage: %s <error_types_csv> <log_dir>" % Path(__file__).name)
