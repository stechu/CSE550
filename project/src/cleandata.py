"""
    cleandata.py : convert null value to -1 and output a single csv.file
    NOTE: output file should be in a different folder in case recursive
    parsing!
"""

import os
import csv
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("folder", help="folder that stores input csvs.")
parser.add_argument("output_file", help="output file name.")
parser.add_argument(
    "default_zero_col", help="the column need null default to zero", type=int)
parser.add_argument(
    "num_cols", help="number of columns of input csvs.", type=int)
args = parser.parse_args()


def clean_data(folder, output_name, zero_col, num_cols):
    # create writer
    output_file = open(output_name, "wb")
    writer = csv.writer(output_file)

    # read csv and do the work
    for fname in os.listdir(folder):
        if fname.endswith(".csv"):
            full_path = "{}/{}".format(folder.rstrip("/"), fname)
            with open(full_path, "rb") as f:
                csvreader = csv.reader(f)
                for line in csvreader:
                    write_line = line
                    for idx, cell in enumerate(write_line):
                        if cell == "":
                            write_line[idx] = -1 if idx != zero_col else 0
                    # sanity checking
                    assert len(write_line) == num_cols
                    # do the write
                    writer.writerow(write_line)

if __name__ == "__main__":
    clean_data(
        args.folder, args.output_file, args.default_zero_col, args.num_cols)
