#!/usr/bin/python3

import datetime
import json
import os
import sys
from abc import ABC
from typing import Callable, Optional

import mega
import mega.errors

UPLOAD_DIRECTORY = "dashboards_backups"


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
        sys.exit(3)

    return directory[0]


class Directory(ABC):
    mega_client = None
    upload_folder = None
    counters = None

    def __init__(  # noqa
        self,
        name: Optional[str],
        capacity: Optional[int],
        counter_max: Optional[int],
        next_directory,
        filename_generator: Callable[[], str],
    ):
        self._name = name
        self._capacity = capacity
        self._counter_max = counter_max
        self._next_directory = next_directory
        self._filename_generator = filename_generator

        if name is not None:
            self._node = get_or_create_directory(
                Directory.mega_client,
                name,
                name
                if Directory.upload_folder is None
                else os.path.join(UPLOAD_DIRECTORY, name),
            )
        else:
            self._node = Directory.upload_folder

    def store(self, file_id, move=False):
        if move:
            self.mega_client.move(
                file_id,
                self._node,
            )
        else:
            self.mega_client.upload(
                file_id,
                self._node,
                self._filename_generator(),
            )


class LastDirectory(Directory):
    def __init__(
        self, filename_generator: Callable[[], str], name: Optional[str] = None
    ):
        super().__init__(name, None, None, None, filename_generator)


class DirectoryWithNext(Directory):
    def __init__(  # noqa
        self,
        name: str,
        capacity: int,
        counter_max: int,
        filename_generator: Callable[[], str],
        next_directory: Directory,
    ):
        super().__init__(
            name, capacity, counter_max, next_directory, filename_generator
        )

    def store(self, file_id, move=False):
        super().store(file_id, move=move)

        stored_files = self.mega_client.get_files_in_node(self._node)
        if len(stored_files) > self._capacity:
            stored_files = list(stored_files.values())
            stored_files.sort(key=lambda f: f["ts"])

            if self.counters.inc(self._name) == self._counter_max:
                self._next_directory.store(stored_files[0]["h"], move=True)
                self.counters.reset(self._name)
            else:
                self.mega_client.destroy(stored_files[0]["h"])

            if move:
                self.mega_client.rename(
                    [None, self.mega_client.find(handle=file_id)],
                    self._filename_generator(),
                )


class Counters:
    def __init__(self):
        try:
            with open("/var/lib/dashboards_backups/counters.json") as counters_file:
                try:
                    self._json = json.load(counters_file)
                except json.decoder.JSONDecodeError:
                    print("Counters file with invalid json format", file=sys.stderr)
                    sys.exit(2)
        except FileNotFoundError:
            print("Counters file not found", file=sys.stderr)
            sys.exit(2)
        except PermissionError:
            print("Not read permission on counters file", file=sys.stderr)
            sys.exit(2)

        if not os.access("/var/lib/dashboards_backups/counters.json", os.W_OK):
            print("Not write permission on counters file", file=sys.stderr)
            sys.exit(2)

        self.updates = False

    def inc(self, name):
        if name not in self._json:
            self._json[name] = 0
        self._json[name] += 1
        self.updates = True
        return self._json[name]

    def reset(self, name):
        self._json[name] = 0
        self.updates = True

    def get(self, name):
        return self._json[name]

    def save(self):
        if self.updates:
            with open(
                "/var/lib/dashboards_backups/counters.json", "w"
            ) as counters_file:
                json.dump(self._json, counters_file)


def main(argc, argv):
    if argc != 3:
        print(
            f"Invalid number of arguments\nUSAGE: {argv[0]} credentials_file upload_file",
            file=sys.stderr,
        )
        sys.exit(1)

    Directory.counters = Counters()

    try:
        with open(argv[1]) as credentials_file:
            email = credentials_file.readline().strip()
            password = credentials_file.readline().strip()
    except FileNotFoundError:
        print(f'Credentials file "{argv[1]}" not found', file=sys.stderr)
        sys.exit(2)

    mega_client = mega.Mega()
    try:
        mega_client.login(email, password)
    except mega.errors.RequestError as err:
        print(f"Error while logging in to Mega. ({err})", file=sys.stderr)
        sys.exit(3)

    if UPLOAD_DIRECTORY:
        upload_folder = get_or_create_directory(
            mega_client, "upload directory", UPLOAD_DIRECTORY
        )
    else:
        upload_folder = None

    Directory.mega_client = mega_client
    Directory.upload_folder = upload_folder

    most_recent_dir = DirectoryWithNext(
        name="week",
        capacity=7,
        counter_max=7,
        filename_generator=lambda: datetime.datetime.now().strftime("%Y%m%d.tar.gz"),
        next_directory=LastDirectory(
            lambda: datetime.datetime.now().strftime("%Y%W.tar.gz")
        ),
    )

    try:
        most_recent_dir.store(argv[2])
    except FileNotFoundError:
        print(f'Upload file "{argv[2]}" not found', file=sys.stderr)
        sys.exit(2)

    Directory.counters.save()


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
