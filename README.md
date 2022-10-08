# [SureMD - Markdown Documentation Tester](https://github.com/embtool/suremd)

by [Djones A. Boni](https://github.com/djboni)

Test the documentation to keep it up to date.

SureMD will find all markdown (.md) files in the subdirectories, create
files and process the console commands.

# Quick-start

Call `suremd.py` and pass the documentation directory (where the
markdown files are present) and the build directory (working directory
where to create files and run commands).

```
$ ./suremd.py . build
README.md OK
```

It is also possible to call `suremd.py` with single markdown file.

```
$ ./suremd.py README.md build
README.md OK
```

By default each file is processed on a different directory created
inside the build directory. Pass `--single-dir` to process everything
in the build directory. This is useful when using relative paths to
files in the version control, alongside de documentation.

```
$ ./suremd.py . build --single-dir
README.md OK
```

# How to use SureMD

1. To create a file use triple ticks followed by the language (```XXX),
   add a comment with the filename (no spaces), the code for
   the file, and end with triple ticks.

```cpp
/* File: main.c */
#include <stdio.h>

int main(void)
{
    printf("Hello, World!\n");
    return 0;
}
```

The first line (filename comment) is removed from the output file.

2. To run a command use triple ticks followed by "console" (```console),
   write the command prepended with a dollar sign.
   Write a comment before the first command (optional).
   Write the expected output after the command (optional).

```console
A command starts with a dollar sign ($).
Anything before the first command is a comment.
Anything after a command must match the command's output.

$ gcc -o main main.c
$ ./main
Hello, World!
```

All commands must succeed (return zero).

3. Change the file, overwriting the previous content.

```cpp
/* File: main.c */
#include <stdio.h>

int main(int argc, char *argv[])
{
    if (argc == 1)
    {
        /* No arguments. */
        printf("Hello, World!\n");
    }
    else
    {
        /* One or more arguments. */
        for (int i = 1; i < argc; i++)
            printf("Hello, %s!\n", argv[i]);
    }

    return 0;
}
```

4. Check many lines in sequence.
   If only part of the output is known use ... as a wildcard.

```console
$ gcc -o main main.c

$ ./main alice $USER bob
Hello, alice!
Hello, ...!
Hello, bob!
```

# TODO

- Unfortunately changing directories is quite limited:

  - The lifespan of changing directory is the command block
  - Can use only actual paths: `cd dir`
  - CANNOT do:

    - CANNOT use wildcards: `cd d*r`
    - CANNOT use variables: `cd $DIR`
    - CANNOT do anything else in the same line: `cd dir; touch file.txt`
