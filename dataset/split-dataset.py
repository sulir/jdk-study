#!/usr/bin/env python3
from os import scandir, renames
from os.path import basename
from os.path import join
from random import shuffle
from sys import argv

PART_DIR = 'projects%d'

def split_dataset(dataset_dir, num_parts):
    projects = [file.path for file in scandir(dataset_dir) if file.is_dir()]
    shuffle(projects)
    parts = [join(dataset_dir, PART_DIR % i) for i in range(1, int(num_parts) + 1)]

    while True:
        for part in parts:
            if len(projects) == 0:
                return
            project = projects.pop()
            renames(project, join(part, basename(project)))

if __name__ == '__main__':
    if len(argv) == 3:
        split_dataset(argv[1], argv[2])
    else:
        print('Usage: %s <dataset_dir> <num_parts>' % basename(__file__))
        exit(1)
