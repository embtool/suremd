#!/usr/bin/env python3

import argparse
import re
import sys
from typing import DefaultDict, List, Tuple
import glob
import os
import subprocess

verbose = False


def parse_command_line() -> Tuple:
    global verbose

    parser = argparse.ArgumentParser(description="Test markdown documentation.")

    parser.add_argument(
        "doc_dir",
        metavar="DOC_DIR",
        type=str,
        nargs=1,
        help="documentation directory",
    )
    parser.add_argument(
        "build_dir",
        metavar="BUILD_DIR",
        type=str,
        nargs=1,
        help="build directory",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="verbose, can be passed multiple times",
    )

    args = parser.parse_args()
    doc_dir = args.doc_dir[0]
    build_dir = args.build_dir[0]
    verbose = args.verbose

    return doc_dir, build_dir


def find_doc_files(dir: str, extension=".md") -> List[str]:
    files = glob.glob(f"{dir}/**/*{extension}", recursive=True)
    abs_file_and_file = [(os.path.abspath(f), f) for f in files]
    return sorted(abs_file_and_file)


def create_directory(dir: str) -> None:
    os.makedirs(dir, exist_ok=True)


class DirStack(list):
    def push_directory(self, dir: str) -> None:
        # Push current directory to the stack
        self.append(os.path.abspath(os.curdir))

        # Create and change directory
        create_directory(dir)
        os.chdir(dir)

    def pop_directory(self) -> None:
        # Pop previous directory from the stack
        dir = self.pop()

        # Change directory
        os.chdir(dir)


def test_file(file_abs: str, file: str, dir_stack: DirStack) -> None:
    replace = "./ "
    test_dir = "".join(map(lambda x: "_" if x in replace else x, file))

    errors = 1

    dir_stack.push_directory(test_dir)
    try:
        errors = try_test_file(file_abs, file, dir_stack)
    finally:
        dir_stack.pop_directory()

    return errors


NOTHING = 0
RUN_COMMAND = 1
COMMAND_OUTPUT = 2
CREATE_FILE = 3
FILE_CONTENT = 4


def try_test_file(file_abs: str, file: str, dir_stack: DirStack) -> None:
    # Read file
    with open(file_abs) as fp:
        content = fp.readlines()

    state = NOTHING
    errors = 0

    for num, line in enumerate(content):
        # Clean leading and trailing whitespace
        stripped = line.strip()

        if stripped == "```":
            # Do according to the previous state

            if state == FILE_CONTENT:
                if dir_name != "":
                    create_directory(dir_name)

                with open(file_name, "w") as fp:
                    fp.write(file_contents)

                del file_name
                del dir_name
                del file_contents

            elif state == COMMAND_OUTPUT:
                del command_line
                del command_stdout
                del command_pos

            state = NOTHING
            continue
        elif stripped == "```console":
            # Run command
            state = RUN_COMMAND
            continue
        elif stripped.startswith("```"):
            # Create file
            state = CREATE_FILE
            continue
        elif state == COMMAND_OUTPUT and line.startswith("$"):
            state = RUN_COMMAND

        if state == RUN_COMMAND:
            try:
                command_line = re.findall(r"^\$\s*(.+)$", line)[0]
            except IndexError:
                continue

            print_info(f"Running command $ {command_line}")

            run = subprocess.run(
                command_line,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            # Check for bad return value
            if run.returncode != 0:
                print_err(
                    f"{file}:{num+1}: command returned error {run.returncode}"
                )
                errors += 1
                state = NOTHING
                continue

            command_stdout = run.stdout.decode()
            command_pos = 0
            del run

            if command_stdout:
                print_debug(f"Command output\n{command_stdout}")

            state = COMMAND_OUTPUT

        elif state == COMMAND_OUTPUT:
            lf = "\n"
            regex = f"^{re.escape(line.rstrip(lf))}$"
            regex = regex.replace(r"\.\.\.", r".*")
            match = re.findall(regex, command_stdout, re.MULTILINE)

            if match:
                print_info(f"Found line {str(line.encode())[1:]}")
            else:
                print_err(f"Could not find line {str(line.encode())[1:]}")
                print_err(
                    f"{file}:{num+1}: line not present in output:\n"
                    f"regex={regex}\n"
                    f"line={line.rstrip(lf)}\n"
                    f"output=\n{command_stdout.rstrip(lf)}\n"
                )
                errors += 1

        elif state == CREATE_FILE:
            try:
                file_name, dir_name = re.findall(
                    #  Start-Comment  File-Name  End-Comment
                    r"^(?:#|//|/\*)\s*(((?:\w+/)*)[\w.]+)\s*(?:\*/)?$",
                    line,
                )[0]
            except IndexError:
                print_err(f"{file}:{num+1}: no file name in the first line")
                state = NOTHING
                errors += 1
                continue

            print_info(f"Creating file {file_name}")

            file_contents = ""

            state = FILE_CONTENT

        elif state == FILE_CONTENT:
            file_contents += line

    if errors == 0:
        print_err(f"{file} OK", start="")
    else:
        print_err(f"{file} FAIL", start="")

    return errors


def print_err(s: str, start="ERROR: ") -> None:
    print(f"{start}{s}\n", end="", file=sys.stderr)


def print_warn(s: str):
    if verbose >= 0:
        print_err(s, start="WARNING: ")


def print_info(s: str):
    if verbose >= 1:
        print_err(s, start="INFO: ")


def print_debug(s: str):
    if verbose >= 2:
        print_err(s, start="DEBUG: ")


def main():
    doc_dir, build_dir = parse_command_line()

    doc_files = find_doc_files(doc_dir)

    dir_stack = DirStack()

    dir_stack.push_directory(build_dir)

    errors = 0
    for file_abs, file in doc_files:
        errors += test_file(file_abs, file, dir_stack)

    dir_stack.pop_directory()

    sys.exit(errors != 0)


if __name__ == "__main__":
    main()
