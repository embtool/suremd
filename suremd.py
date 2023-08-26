#!/usr/bin/env python3

import argparse
import difflib
import re
import sys
from typing import List, Tuple
import glob
import os
import subprocess

verbose = 0
single_dir = False
stop_on_error = True
format_enabled_for = set()
file_string = "File"


def parse_command_line() -> Tuple:
    global verbose
    global single_dir
    global stop_on_error
    global format_enabled_for
    global file_string

    parser = argparse.ArgumentParser(
        description="""
    SureMD - Test markdown files.
    Create files and execute commands in markdown files (.md).
    See https://github.com/embtool/suremd for information on how to
    create files that SureMD can process.
    """
    )

    parser.add_argument(
        "doc_path",
        metavar="DOC_PATH",
        type=str,
        nargs="*",
        default=["."],
        help="directories or markdown files (default: ./)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="verbose, can be passed multiple times",
    )
    parser.add_argument(
        "--build-dir",
        type=str,
        nargs=1,
        default=["./build"],
        help="build directory (default: ./build/)",
    )
    parser.add_argument(
        "--single-dir",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="single directory, do not create directories for each file",
    )
    parser.add_argument(
        "--stop-on-error",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="stop on the first error",
    )
    parser.add_argument(
        "-f",
        "--format",
        action="append",
        default=[],
        help="comma-separated list of extensions to format ("
        "c,h,cpp: clang-format; "
        "cmake: cmake-format; "
        "py: black; "
        "sh: shfmt; "
        "all: for all"
        ")",
    )
    parser.add_argument(
        "--file-string",
        action="store",
        default="File",
        help='change the filename string (default: "File")',
    )

    args = parser.parse_args()
    doc_path = args.doc_path
    build_dir = args.build_dir[0]
    verbose = args.verbose
    single_dir = args.single_dir
    stop_on_error = args.stop_on_error
    format_enabled_for = {
        ext for block in args.format for ext in block.split(",")
    }
    file_string = args.file_string

    return doc_path, build_dir


def find_doc_files(list_of_paths: List[str], extension=".md") -> List[str]:

    files = []

    for path in list_of_paths:
        if os.path.isfile(path):
            files += [path]
        elif os.path.isdir(path):
            files += glob.glob(f"{path}/**/*{extension}", recursive=True)
        else:
            raise RuntimeError(f"ERROR: {path} does not exist.")

    files = {f if os.path.isabs(f) else os.path.relpath(f, ".") for f in files}
    abs_file_and_file = {(os.path.abspath(f), f) for f in files}
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

    def top_directory(self) -> str:
        # Get the top directory
        dir = self[-1]
        return dir


def os_dependent_pwd() -> str:
    """
    Append and OS dependent command that prints a new line and the
    current working directory. We need to make sure keep the
    same return value as the previous command. Example of
    the expected output: "\n@SureMD_PWD@=/home/user\n"
    """
    return (
        "\n"
        "SureMD_RETVAL=$?\n"
        "echo\n"
        'echo "@SureMD_PWD@=$PWD"\n'
        "exit $SureMD_RETVAL\n"
    )


def test_file(file_abs: str, file: str, dir_stack: DirStack) -> None:
    replace = "./ "

    if single_dir:
        # Single directory, just push the current directory to the stack
        test_dir = "."
    else:
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
FAILING_COMMAND = 5


def try_test_file(file_abs: str, file: str, dir_stack: DirStack) -> None:
    # Read file
    with open(file_abs) as fp:
        content = fp.readlines()

    state = NOTHING
    errors = 0

    # Make sure the directory stack is not leaking
    starting_dir_stack_len = len(dir_stack)

    for num, line in enumerate(content):
        # Clean leading and trailing whitespace
        stripped = line.strip()
        file_line = f"{file}:{num+1}"

        if stripped == "```":
            # Do according to the previous state

            if state == NOTHING:
                # Do nothing
                pass
            elif state == FILE_CONTENT:
                if dir_name != "":
                    create_directory(dir_name)

                with open(file_name, "w") as fp:
                    fp.write(file_contents)

                # Check formatting
                check_formatting(file_name, file_contents, file_line)

                del file_name
                del dir_name
                del anonymous_file
                del anonymous_extension
                del file_contents

            elif state == COMMAND_OUTPUT:
                del command_line
                del command_stdout
                del command_output_pos

                # Restore previous directory. The command block might
                # have changed directory.
                dir_stack.pop_directory()

            elif state in (RUN_COMMAND, FAILING_COMMAND):
                # Restore previous directory. The command block might
                # have changed directory.
                dir_stack.pop_directory()

                if stop_on_error:
                    break

            state = NOTHING
            continue
        elif stripped == "```console":
            # Run command
            state = RUN_COMMAND
            # Save current directory. The command block can change it.
            dir_stack.push_directory(os.getcwd())
            continue
        elif stripped.startswith("```"):
            # Create file
            state = CREATE_FILE
            anonymous_extension = stripped[3:]
            continue
        elif state == COMMAND_OUTPUT and line.startswith("$"):
            state = RUN_COMMAND

        if state == RUN_COMMAND:
            try:
                command_line = re.findall(r"^\$\s*(.+)$", line)[0]
            except IndexError:
                continue

            print_info(f"Running command $ {command_line}")

            # Append a command that prints the current working directory
            command_line_pwd = command_line + os_dependent_pwd()

            run = subprocess.run(
                command_line_pwd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            # Filter the last line, which is the working directory at
            # the end of the command
            command_output_pos = 0
            output_lines = run.stdout.decode().split("\n")
            if len(output_lines) < 2 or not output_lines[-2].startswith(
                "@SureMD_PWD@="
            ):
                # The execution did not reach the end of the command,
                # where the working directory is printed.
                # This may be caused by and `exit` in the command.
                # In this case we keep the previous working directory.
                command_stdout = "\n".join(output_lines)
            else:
                dir = output_lines[-2][13:]
                command_stdout = "\n".join(output_lines[:-3])

                # Change directory
                cwd = os.getcwd()
                if dir != cwd:
                    base_dir = dir_stack.top_directory()
                    print_info(
                        f'Changing directory to "{os.path.relpath(dir, base_dir)}"'
                    )
                    os.chdir(dir)

            s = f"Command output\n{command_stdout}"

            # Check for bad return value
            if run.returncode != 0:
                print_err(
                    f"{file_line}: command '{command_line}' returned error {run.returncode}"
                )
                if command_stdout:
                    print_err(s)
                errors += 1
                state = FAILING_COMMAND
            else:
                if command_stdout:
                    print_info(s)
                state = COMMAND_OUTPUT

        elif state == COMMAND_OUTPUT:
            lf = "\n"
            line = line.rstrip(lf)
            if line == "":
                continue

            regex = f"^\s*{re.escape(line)}\s*$"
            # Substitute "SPACES...SPACES" for ".*"
            regex = re.sub(r"(\\?\s)*\\\.\\\.\\\.(\\?\s)*", r".*", regex)
            match = re.search(
                regex, command_stdout[command_output_pos:], re.MULTILINE
            )

            if match:
                print_info(f"Found line {str(line.encode())[1:]}")
                print_debug(
                    f"Found line {str(line.encode())[1:]} in the output {command_stdout[command_output_pos:].encode()}"
                )
                command_output_pos += match.span()[1]
            else:
                print_err(f"Could not find line {str(line.encode())[1:]}")
                print_debug(
                    f"Could not find line {str(line.encode())[1:]} in the output {command_stdout[command_output_pos:].encode()}"
                )
                print_err(
                    f"{file_line}: line not present in output:\n"
                    f"regex={regex}\n"
                    f"line={line}\n"
                    f"pos={command_output_pos}\n"
                    f"output=\n{command_stdout.rstrip(lf)}\n"
                )
                errors += 1
                state = FAILING_COMMAND

        elif state == CREATE_FILE:
            try:
                file_name, dir_name = re.findall(
                    #  Start-Comment File-String: Optional-Dir/File-Name Optional-End-Comment
                    r"^\S*\s*"
                    + re.escape(file_string)
                    + r":\s+(((?:\w+/)*)[\w.]+)\s*.*$",
                    line,
                )[0]
                anonymous_file = False
                print_info(f"Creating file {file_name}")

                file_contents = ""
            except IndexError:
                # No file name in the first line
                # Do not create but try to format
                file_name = f"anonymous-file-line-{num+1}.{anonymous_extension}"
                dir_name = ""
                anonymous_file = True
                print_info(f"Anonymous file {file_name}")

                file_contents = line

            state = FILE_CONTENT

        elif state == FILE_CONTENT:
            file_contents += line

    if errors == 0:
        print_err(f"{file} OK", start="")
    else:
        print_err(f"{file} FAIL", start="")

    # Make sure the directory stack is not leaking
    assert len(dir_stack) == starting_dir_stack_len, (
        "Directory stack is leaking. It should not grow or shrink!\n"
        f"dir_stack={str(dir_stack)}\n"
        f"file={file_abs}"
    )

    return errors


def check_formatting(
    file_name: str, file_contents: str, md_file_line: str
) -> None:
    if "." not in file_name:
        # Unknown (no extension)
        return

    if file_name == "CMakeLists.txt":
        extension = "cmake"
    else:
        extension = file_name.split(".")[-1]

    if extension not in format_enabled_for and "all" not in format_enabled_for:
        # Should not format this type of ile
        return

    in_place_formatting = False

    if extension in {"c", "h", "cpp"}:
        # C/C++
        formatter_command = ["clang-format"]
    elif extension in {"cmake"}:
        # CMake
        formatter_command = ["cmake-format", "-"]
    elif extension in {"zig"}:
        # Zig
        formatter_command = ["zig", "fmt"]
        in_place_formatting = True
    elif extension in {"py"}:
        # Python
        formatter_command = ["black", "-"]
    elif extension in {"sh"}:
        # Shell
        formatter_command = ["shfmt", "-i=4", "-"]
    else:
        # Unknown
        print_info(f"Ignoring formatting of unknown file type {md_file_line}: {file_name}")

    if in_place_formatting:
        formatter = subprocess.run(
            formatter_command + [file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        with open(file_name) as fp:
            formatted_contents = fp.read()
    else:
        formatter = subprocess.run(
            formatter_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=file_contents.encode(),
        )

        formatted_contents = formatter.stdout.decode()

    diff_contents = "\n".join(
        difflib.unified_diff(
            file_contents.split("\n"),
            formatted_contents.split("\n"),
            fromfile=f"a/{file_name}",
            tofile=f"b/{file_name}",
            lineterm="",
        )
    )

    if file_contents != formatted_contents:
        print_warn(
            f"Formatting error: {md_file_line}: {file_name}\n{diff_contents}"
        )


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
    doc_path, build_dir = parse_command_line()

    doc_files = find_doc_files(doc_path)

    dir_stack = DirStack()

    dir_stack.push_directory(build_dir)

    errors = 0
    for file_abs, file in doc_files:
        errors += test_file(file_abs, file, dir_stack)

        if errors > 0 and stop_on_error:
            break

    dir_stack.pop_directory()

    sys.exit(errors != 0)


if __name__ == "__main__":
    main()
