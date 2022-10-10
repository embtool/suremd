# Creating Files

To create a file:

- Start a code block with triple ticks followed by the file type (```py)
- The first line must have the file name (# File: filename)
  - No spaces are allowed in the file name
- Add the file code
- End the code block with triple ticks (```)

```py
# File: hello.py
#!/usr/bin/env python3
print("Hello")
```

Starting a code block with triple ticks, but **without the type** (```)
does NOT create a file.

If you want a monospaced block of text that is the way to go.

```
# File no-file-is-created.txt
This does not create a file because the type is missing after the triple
ticks.
```
