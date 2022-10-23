import unrealsdk
import argparse
from typing import Optional

from Mods.CommandExtensions import RegisterConsoleCommand
from Mods.CommandExtensions.builtins import obj_name_splitter, parse_object, is_obj_instance
from Mods.CommandExtensions.builtins.clone import parse_clone_target, clone_object

def clone_title(
    src: unrealsdk.UObject,
    outer: Optional[unrealsdk.UObject],
    name: str
) -> Optional[unrealsdk.UObject]:
    cloned = clone_object(src, outer, name)
    if cloned is None:
        return None

    Cloned_CustomPresentations = []
    for idx, Presentation in enumerate(src.CustomPresentations):
        Cloned_CustomPresentations.append(clone_object(Presentation, cloned, f"{Presentation.Class.Name}_{idx}"))
    setattr(cloned, "CustomPresentations", Cloned_CustomPresentations)
    return cloned

def handler(args: argparse.Namespace) -> None:
    src = parse_object(args.base)
    if src is None:
        return
    outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
    if name is None:
        return
    if is_obj_instance(src, "WeaponNamePartDefinition") or is_obj_instance(src, "ItemNamePartDefinition"):
        clone_title(src, outer, name)
    else:
        unrealsdk.Log(f"Object {src.PathName(src)} must be a 'AttributeDefinition'!")
        return


parser = RegisterConsoleCommand(
    "clone_title",
    handler,
    splitter=obj_name_splitter,
    description="Creates a clone of an existing object."
)
parser.add_argument("base", help="The object to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
parser.add_argument(
    "-x", "--suppress-exists",
    action="store_true",
    help="Suppress the error message when an object already exists."
)
