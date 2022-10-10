# Complete Example

We can do a lot with just creating files and executing commands.

As an example, let's create a Python program that greets all of its
arguments.

```py
# File: hello.py
#!/usr/bin/env python3
import sys

for arg in sys.argv:
    print(f"Hello {arg}!")
```

Now let's test the program's output.

We can run the file by calling the Python interpreter.

```console
$ python3 hello.py Alice
Hello Alice!
```

And we can make it executable and let the Shell figure out it should
use Python to interpret it.

```console
$ chmod +x hello.py
$ ./hello.py Bob
Hello Bob!
```

If we only know part of the output, we can use "..." as a wildcard.

```console
$ ./hello.py $USER
Hello ...!
```

Several lines of output can be tested at the same time.

```console
$ ./hello.py Alice $USER Bob
Hello Alice!
Hello ...!
Hello Bob!
```
