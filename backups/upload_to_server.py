#!/usr/bin/python3

import datetime
import pathlib
import os
import sys

import mega

UPLOAD_DIRECTORY = "dashboards_backups"
CURRENT_WEEK_DIRECTORY = "current_week"


def get_or_create_directory(m: mega.Mega, name: str, path: str):
    """
    :param m: Mega object
    :param name: name of the directory to upload. Used for error messages
    :param path: path to the directory to get or create
    """
    directory = m.find(path)
    if not directory:
        return m.create_folder(path)[os.path.basename(path)]

    if directory[1]["t"] != 1:  # if its not a directory
        print(
            f"Node on the {name} directory provided is not a directory.",
            file=sys.stderr,
        )
        sys.exit(4)

    return directory[0]


def main(argc, argv):
    if argc != 3:
        print(
            f"Invalid number of arguments\nUSAGE: {argv[0]} credentials_file upload_file",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(argv[1]) as credentials_file:
            email = credentials_file.readline().strip()
            password = credentials_file.readline().strip()
    except FileNotFoundError:
        print(f'Credentials file "{argv[1]}" not found', file=sys.stderr)
        sys.exit(2)

    m = mega.Mega()
    try:
        m.login(email, password)
    except mega.errors.RequestError as err:
        print(f"Error while logging in to Mega. ({err})", file=sys.stderr)
        sys.exit(3)

    if UPLOAD_DIRECTORY:
        upload_folder = get_or_create_directory(m, "upload directory", UPLOAD_DIRECTORY)
    else:
        upload_folder = None

    current_week = get_or_create_directory(
        m,
        "current week",
        CURRENT_WEEK_DIRECTORY
        if upload_folder is None
        else os.path.join(UPLOAD_DIRECTORY, CURRENT_WEEK_DIRECTORY),
    )

    current_week_files = m.get_files_in_node(current_week)
    if len(current_week_files) == 6:
        # if we already got 6 files on the current week directory
        #  then the current file is the the final one for this week

        extension = "".join(pathlib.Path(argv[2]).suffixes)
        try:
            m.upload(
                argv[2],
                upload_folder,
                datetime.datetime.now().strftime("%Y%W") + extension,  # YearWeek.tar.gz
            )
        except FileNotFoundError:
            print(f'Upload file "{argv[2]}" not found', file=sys.stderr)
            sys.exit(3)

        for file in current_week_files:
            m.delete(file)
        m.empty_trash()
    else:
        try:
            m.upload(argv[2], current_week)
        except FileNotFoundError:
            print(f'Upload file "{argv[2]}" not found', file=sys.stderr)
            sys.exit(3)


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
