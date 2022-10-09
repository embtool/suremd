# [SureMD - Test Markdown Files](https://github.com/embtool/suremd)

by [Djones A. Boni](https://github.com/djboni)

SureMD will find all markdown files (.md) in the subdirectories and
process them, creating the files and running the console commands
specified in the documentation.

# Quick-start

Just call `suremd.py`. It will search for markdown files in the current
working directory and will process them in the _build/_ directory.

```
$ ./suremd.py
```

It is also possible to call `suremd.py` with directories and markdown
files.

```
$ ./suremd.py README.md
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
