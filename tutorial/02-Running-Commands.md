# Running Commands

To run a command:

- Start a code block with triple ticks followed by "console" (```console)
- The lines before the first command are comments
- A command starts with dollar sign "$" followed by the actual command
  to be executed
  - The command must succeed (return status must be 0)
  - The lines following a command are used to check its output
  - Use triple dots "..." as a wildcard to match the output
- End the code block with triple ticks (```)

```console
This is a comment, you can explain the commands that will run.
The first command writes "TEST 1".
The second command writes "TEST 2", which is verified.
The third commands writes three greetings, which are verified in order
and the second greet uses "..." as a wildcard.

$ echo TEST 1
$ echo TEST 2
TEST 2

$ echo Hi alice; echo Hi $USER; echo Hi bob
Hi alice
Hi ...
Hi bob
```

Starting a code block with triple ticks, but **without "console"** (```)
does NOT execute commands.

If you want a monospaced block of text that is the way to go.

```
This does not run any commands because "console" is missing after the
triple ticks.

$ echo "This does not run"
```
