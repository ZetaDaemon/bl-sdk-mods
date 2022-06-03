# Table of Contents
- [`clone_bal`](#clone_bal)
- [`clone_bpd_skill`](#clone_bpd_skill)

## `clone_bal`
usage: `clone_bal [-h] [-x] [-b] base clone`

Creates a clone of an existing balance as well as the part lists, manually dump the new balance to check the name of the part lists.

| positional arguments | |
|:---|:---|
| `base`  | The object to create a copy of. |
| `clone` | The name of the clone to create. |

| optional arguments | |
|:---|:---|
| `-h, --help` | Show this help message and exit |
| `-x, --suppress-exists` | Suppress the error message when an object already exists. |
| `-b, --use-base` | Use the original object as the base definition of the new balance rather than keeping the same base definition as the original balance |

## `clone_bpd_skill`
usage: `clone_bpd_skill [-h] [-x] base clone skill`

Creates a clone of a BehaviourProvidierDefinition, as well as recursively cloning some of the
objects making it up. This may not match the exact layout of the original objects, dump them
manually to check what their new names are. Uses a base name for skills to more neatly handle the names for the skills created, for example if you use `GD_Weap_SMG.Skills.Skill_NewSkill` for the skill argument, the created skills will look like `GD_Weap_SMG.Skills.Skill_NewSkill`, `GD_Weap_SMG.Skills.Skill_NewSkill_0` ect.

Also, this command is just a reworked version of `clone_bpd` in command extentions so credit to apple for doing that, I've just added the extra skill naming logic.

| positional arguments | |
|:---|:---|
| `base`  | The object to create a copy of. |
| `clone` | The name of the clone to create. |
| `skill` | The name of the skill to use as the base for all created skills. |

| optional arguments | |
|:---|:---|
| `-h, --help` | Show this help message and exit |
| `-x, --suppress-exists` | Suppress the error message when an object already exists. |

## `clone_attr`
usage: `clone_bal [-h] [-x] [-d] base clone`

Clones an attribute as well as the resolver chains, manually dump the new attribute to check the name of the resolver chains.

| positional arguments | |
|:---|:---|
| `base`  | The object to create a copy of. |
| `clone` | The name of the clone to create. |

| optional arguments | |
|:---|:---|
| `-h, --help` | Show this help message and exit |
| `-x, --suppress-exists` | Suppress the error message when an object already exists. |
| `-d, --use-base` | Uses the ObjectArchetype of the base objects to create the clones rather than the base objects themselves |