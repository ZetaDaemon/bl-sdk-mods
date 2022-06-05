import unrealsdk
import argparse
import functools
from typing import Callable, Dict

from Mods.CommandExtensions import RegisterConsoleCommand
from Mods.CommandExtensions.builtins import is_obj_instance, obj_name_splitter, parse_object
from Mods.CommandExtensions.builtins.clone import clone_object, parse_clone_target

"""
We pass a known clones dict between functions so that we don't clone the same object twice (if it's
stored in two different locations)
"""
ClonesDict = Dict[unrealsdk.UObject, unrealsdk.UObject]

suppress_exists = False;
skill_idx = -1

# There are a bunch of different fields skills can be stored in, hence the field arg
def fixup_skill_field(field: str, behavior: unrealsdk.UObject, known_clones: ClonesDict, clone_skill_base: list) -> None:
    global suppress_exists
    global skill_idx
    skill = getattr(behavior, field)
    if skill is None:
        return
    if skill in known_clones:
        setattr(behavior, field, known_clones[skill])
        return
    full_name = clone_skill_base[1] if skill_idx < 0 else f"{clone_skill_base[1]}_{skill_idx}"

    unrealsdk.Log(f"Cloning new skill")
    unrealsdk.Log(f"Base: {skill}")
    unrealsdk.Log(f"Outer: {clone_skill_base[0]}")
    unrealsdk.Log(f"Name: {full_name}")
    cloned_skill = clone_object(
        skill,
        clone_skill_base[0],
        full_name
    )
    if cloned_skill is None:
        return
    skill_idx = skill_idx + 1
    known_clones[skill] = cloned_skill

    setattr(behavior, field, cloned_skill)

    bpd = cloned_skill.BehaviorProviderDefinition
    if bpd is None:
        return

    if bpd in known_clones:
        cloned_skill.BehaviorProviderDefinition = known_clones[bpd]
        return

    cloned_bpd = clone_object(
        bpd,
        cloned_skill,
        "" if bpd.Name == bpd.Class.Name else bpd.Name
    )
    if cloned_bpd is None:
        return
    known_clones[bpd] = cloned_bpd

    cloned_skill.BehaviorProviderDefinition = cloned_bpd
    fixup_bpd(cloned_bpd, known_clones, clone_skill_base)

def fixup_AE_field(field: str, behavior: unrealsdk.UObject, known_clones: ClonesDict, clone_skill_base: list) -> None:
    skill = getattr(behavior, field)
    if skill is None:
        return

    if skill in known_clones:
        setattr(behavior, field, known_clones[skill])
        return

    cloned_skill = clone_object(
        skill,
        behavior,
        # Empty string gives us the auto numbering back
        "" if skill.Name == skill.Class.Name else skill.Name
    )
    if cloned_skill is None:
        return
    known_clones[skill] = cloned_skill

    setattr(behavior, field, cloned_skill)

    bpd = cloned_skill.BehaviorProviderDefinition
    if bpd is None:
        return

    if bpd in known_clones:
        cloned_skill.BehaviorProviderDefinition = known_clones[bpd]
        return

    cloned_bpd = clone_object(
        bpd,
        cloned_skill,
        "" if bpd.Name == bpd.Class.Name else bpd.Name
    )
    if cloned_bpd is None:
        return
    known_clones[bpd] = cloned_bpd

    cloned_skill.BehaviorProviderDefinition = cloned_bpd
    fixup_bpd(cloned_bpd, known_clones, clone_skill_base)


# Mapping behavior class names to functions that perform extra fixup on them
extra_behaviour_fixups: Dict[str, Callable[[unrealsdk.UObject, ClonesDict], str]] = {
    "Behavior_AttributeEffect": functools.partial(fixup_AE_field, "AttributeEffect"),
    "Behavior_ActivateSkill": functools.partial(fixup_skill_field, "SkillToActivate"),
    "Behavior_DeactivateSkill": functools.partial(fixup_skill_field, "SkillToDeactivate"),
    "Behavior_ActivateListenerSkill": functools.partial(fixup_skill_field, "SkillToActivate")
}


def fixup_bpd(cloned: unrealsdk.UObject, known_clones: ClonesDict, clone_skill_base: list) -> None:
    try:
        for sequence in cloned.BehaviorSequences:
            # There are a bunch of other fields, but this seems to be the only used one
            try:
                for data in sequence.BehaviorData2:
                    behavior = data.Behavior
                    if behavior is None:
                        continue

                    if behavior in known_clones:
                        data.Behavior = known_clones[behavior]
                        continue

                    cloned_behavior = clone_object(
                        behavior,
                        cloned,
                        "" if behavior.Name == behavior.Class.Name else behavior.Name
                    )
                    if cloned_behavior is None:
                        continue
                    known_clones[behavior] = cloned_behavior

                    data.Behavior = cloned_behavior

                    for cls, fixup in extra_behaviour_fixups.items():
                        if is_obj_instance(cloned_behavior, cls):
                            fixup(cloned_behavior, known_clones, clone_skill_base)
            except:
                unrealsdk.Log(f"clone_bpd_skill: Error on line 120")
    except:
        unrealsdk.Log(f"clone_bpd_skill: Error on line 117")


def handler(args: argparse.Namespace) -> None:
    global suppress_exists
    global skill_idx
    skill_idx = -1
    suppress_exists = args.suppress_exists
    src = parse_object(args.base)
    if src is None:
        return
    if not is_obj_instance(src, "BehaviorProviderDefinition"):
        unrealsdk.Log(f"Object {src.PathName(src)} must be a 'BehaviorProviderDefinition'!")
        return

    outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
    if name is None:
        return

    cloned = clone_object(src, outer, name)
    if cloned is None:
        return

    #clone_skill_base = ["", ""]
    clone_skill_base = parse_clone_target(args.skill, "SkillDefinition", suppress_exists)
    fixup_bpd(cloned, {}, clone_skill_base)


parser = RegisterConsoleCommand(
    "clone_bpd_skill",
    handler,
    splitter=obj_name_splitter,
    description=(
        "Creates a clone of a BehaviourProvidierDefinition, as well as recursively cloning some of"
        " the objects making it up. This may not match the exact layout of the original objects,"
        " dump them manually to check what their new names are."
    )
)
parser.add_argument("base", help="The bpd to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
parser.add_argument("skill", help="The name to use as the base for skills")
parser.add_argument(
    "-x", "--suppress-exists",
    action="store_true",
    help="Suppress the error message when an object already exists."
)
