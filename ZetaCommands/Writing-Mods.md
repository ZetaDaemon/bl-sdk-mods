# Table of Contents
- [`clone_bal`](#clone_bal)

## `clone_bal`
usage: `clone_bal [-h] [-x] [-b] base clone`

Creates a clone of an existing balance as well as the part lists, manually dump the new balance to check the name of the part lists.

| positional arguments | |
|:---|:---|
| `base`  | The object to create a copy of. |
| `clone` | The name of the clone to create. |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |
| `-x, --suppress-exists` | Suppress the error message when an object already exists. |
| `-b, --use-base` | Use the original object as the base definition of the new balance rather than keeping the same base definition as the original balance |
