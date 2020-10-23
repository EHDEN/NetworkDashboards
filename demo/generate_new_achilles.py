
import argparse
import csv
import json
import random

override_ranges = {
    # 1: (0, 1) forces the range of the analysis 1 to be between 0 and 1
}


def main(args):
    file_based_ranges = dict()

    if args.override_file:
        with open(args.override_file) as override_file:
            override_ranges = json.loads(override_file.read())

    with open(args.achilles_results_filename) as achilles_results_file:
        reader = csv.reader(achilles_results_file)
        for line in reader:
            id, s1, s2, s3, s4, s5, count = line
            count = int(count)

            min, max = file_based_ranges.get(id, (float("inf"), float("-inf")))

            updates = False
            if count < min:
                min = count
                updates = True
            if count > max:
                max = count
                updates = True

            if updates:
                file_based_ranges[id] = (min, max)

        achilles_results_file.seek(0)

        with open(args.output_file, "w") as output:
            writer = csv.writer(output)
            for line in reader:
                id, s1, s2, s3, s4, s5, count = line

                min, max = override_ranges.get(id, file_based_ranges[id])

                writer.writerow([
                    id,
                    s1,
                    s2,
                    s3,
                    s4,
                    s5,
                    random.randint(min, max)
                ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates a new achilles results by"
                    "generating random values for each set of analysis_id and stratums"
                    "within ranges calculated from a base achilles results file. "
                    "It is possible to override the ranges of the base file either by "
                    "updating the dictionary present on the source code or using the "
                    "--override-from-file option and give a json file with the ranges"
    )

    parser.add_argument(
        "--override-from-file",
        dest="override_file",
        help="json file with ranges for each analysis_id to override the ones "
             "calculated from the base file",
    )

    parser.add_argument(
        "achilles_results_filename",
        help="file to calculate the ranges of random values for each analysis id",
    )
    parser.add_argument(
        "output_file",
        help="output file with the new generated achilles results",
    )

    args = parser.parse_args()

    main(args)
