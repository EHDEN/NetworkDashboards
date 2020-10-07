#!/usr/bin/python3

import mega
import sys


UPLOAD_FOLDER = "dashboards_backups"


def main(argc, argv):
    if argc != 3:
        print(f"Invalid number of arguments\nUSAGE: {argv[0]} credentials_file upload_file", file=sys.stderr)
        exit(1)

    try:
        with open(argv[1]) as credentials_file:
            email = credentials_file.readline().strip()
            password = credentials_file.readline().strip()
    except FileNotFoundError:
        print(f'Credentials file "{argv[1]}" not found', file=sys.stderr)
        exit(2)

    m = mega.Mega()
    try:
        m.login(email, password)
    except mega.errors.RequestError as err:
        print(f"Error while logging in to Mega. ({err})", file=sys.stderr)
        exit(3)

    if UPLOAD_FOLDER:
        upload_folder = m.find(UPLOAD_FOLDER)
        if not upload_folder:
            upload_folder = m.create_folder(UPLOAD_FOLDER)[UPLOAD_FOLDER]
        else:
            upload_folder = upload_folder[0]
    else:
        upload_folder = None

    try:
        m.upload(argv[2], upload_folder)
    except FileNotFoundError:
        print(f'Upload file "{argv[2]}" not found', file=sys.stderr)
        exit(3)


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
