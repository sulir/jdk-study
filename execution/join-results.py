#!/usr/bin/env python3
from pathlib import Path
from sys import argv, path
path.insert(1, str(Path(__file__).resolve().parent.parent))
from common import RESULTS_CSV

def join_results(source_dirs, target_dir):
    target_dir.mkdir(parents=True, exist_ok=True)

    for source_dir in source_dirs:
        append_csv(source_dir / RESULTS_CSV, target_dir / RESULTS_CSV)
        (source_dir / RESULTS_CSV).unlink()
        move_logs(source_dir, target_dir)
        source_dir.rmdir()

def append_csv(source, target):
    with open(source, 'r') as in_csv, open(target, 'a') as out_csv:
        if out_csv.tell() != 0:
            _skip_header = in_csv.readline()
        for line in in_csv:
            out_csv.write(line.rstrip() + '\n')

def move_logs(source_dir, target_dir):
    for item in source_dir.iterdir():
        if item.is_dir():
            item.rename(target_dir / item.name)

if __name__ == '__main__':
    if len(argv) >= 3:
        join_results([Path(d) for d in argv[1:-1]], Path(argv[-1]))
    else:
        print('Usage: %s <source_dir_1>... <target_dir>' % Path(__file__).name)
        exit(1)
