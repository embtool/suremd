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

To learn how to use SureMD take a look into the files in the _tutorial/_
directory. Here is one example:

1. To create a file use triple ticks followed by the language (```XXX),
   add a comment with the filename (no spaces), the code for
   the file, and end with triple ticks.

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

The first line (filename comment) is removed from the output file.

2. To run a command use triple ticks followed by "console" (```console),
   write the command prepended with a dollar sign.
   Write a comment before the first command (optional).
   Write the expected output after the command (optional).
   All commands must succeed (return zero).

```console
$ gcc -o main main.c

$ ./main
Hello, World!

$ ./main alice $USER bob
Hello, alice!
Hello, ...!
Hello, bob!
```
