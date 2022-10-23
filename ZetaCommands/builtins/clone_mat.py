import unrealsdk
import argparse
from typing import Optional, Tuple

from Mods.CommandExtensions import RegisterConsoleCommand
from Mods.CommandExtensions.builtins import obj_name_splitter, parse_object, re_obj_name
from Mods.CommandExtensions.builtins.clone import parse_clone_target


def clone_skin(
    src: unrealsdk.UObject,
    outer: Optional[unrealsdk.UObject],
    name: str
) -> Optional[unrealsdk.UObject]:
    cloned = unrealsdk.ConstructObject(
        Class=src.Class,
        Outer=outer,
        Name=name,
        Template=src.Template
    )
    if cloned is None:
        return None

    cloned.SetParent(src)
    unrealsdk.KeepAlive(cloned)
    cloned.ObjectArchetype = src.ObjectArchetype
    # Don't ask me what on earth this means, but it lets you reference objects cross package
    cloned.ObjectFlags.B |= 4
    return cloned

def clone_mat(
    src: unrealsdk.UObject,
    outer: Optional[unrealsdk.UObject],
    name: str,
    skin_outer: Optional[unrealsdk.UObject],
    skin_name: str
) -> Optional[unrealsdk.UObject]:
    cloned = unrealsdk.ConstructObject(
        Class=src.Class,
        Outer=outer,
        Name=name,
        Template=src
    )
    if cloned is None:
        return None

    unrealsdk.KeepAlive(cloned)
    cloned.ObjectArchetype = src.ObjectArchetype
    # Don't ask me what on earth this means, but it lets you reference objects cross package
    cloned.ObjectFlags.B |= 4
    
    cloned_skin = clone_skin(src.Material, skin_outer, skin_name)
    setattr(cloned, "Material", cloned_skin)
    return cloned

def handler(args: argparse.Namespace) -> None:
    src = parse_object(args.base)
    if src is None:
        return
    outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
    if name is None:
        return
    
    if(src.Class.Name == "WeaponPartDefinition" or src.Class.Name == "ShieldPartDefinition" or src.Class.Name == "GrenadeModPartDefinition"):
        skin_outer, skin_name = parse_clone_target(args.skin, src.Material.Class.Name, args.suppress_exists)
        if skin_name is None:
            return
        clone_mat(src, outer, name, skin_outer, skin_name)
    else:
        clone_skin(src, outer, name)


parser = RegisterConsoleCommand(
    "clone_mat",
    handler,
    splitter=obj_name_splitter,
    description="Creates a clone of an existing material."
)
parser.add_argument("base", help="The object to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
parser.add_argument("skin", nargs='?', default="", help="The name of the skin to create.")
parser.add_argument(
    "-x", "--suppress-exists",
    action="store_true",
    help="Suppress the error message when an object already exists."
)
