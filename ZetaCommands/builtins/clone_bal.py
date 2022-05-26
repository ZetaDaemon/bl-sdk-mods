import unrealsdk
import argparse
import functools
from typing import Callable, Dict

from Mods.CommandExtensions import RegisterConsoleCommand
from Mods.CommandExtensions.builtins import is_obj_instance, obj_name_splitter, parse_object
from Mods.CommandExtensions.builtins.clone import clone_object, parse_clone_target

PLC = ":PartList"
RPLC = ":WeaponPartListCollectionDefinition"
IPLC = ":ItemPartListCollectionDefinition"

def handler(args: argparse.Namespace) -> None:
	src = parse_object(args.base)
	if src is None:
		return
	if not is_obj_instance(src, "InventoryBalanceDefinition"):
		unrealsdk.Log(f"Object {src.PathName(src)} must be a 'InventoryBalanceDefinition'!")
		return

	outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
	cloned = clone_object(src, outer, name)

	if is_obj_instance(src, "WeaponBalanceDefinition"):
		cloned_WeaponPartListCollection = clone_object(src.WeaponPartListCollection, src, name+PLC)
		cloned_RuntimePartListCollection = clone_object(src.RuntimePartListCollection, src, name+RPLC)

		cloned.WeaponPartListCollection = cloned_WeaponPartListCollection
		cloned.RuntimePartListCollection = cloned_RuntimePartListCollection

	elif is_obj_instance(src, "ClassModBalanceDefinition"):
		cloned_ItemPartListCollection = clone_object(src.ItemPartListCollection, src, name+PLC)
		cloned_RuntimePartListCollection = clone_object(src.RuntimePartListCollection, src, name+IPLC)

		cloned.ItemPartListCollection = cloned_ItemPartListCollection
		cloned.RuntimePartListCollection = cloned_RuntimePartListCollection

	elif not src.PartListCollection is None:
		cloned_ItemPartListCollectionDefinition = clone_object(src.PartListCollection, src, name+IPLC)
		cloned.PartListCollection = cloned_ItemPartListCollectionDefinition

	if not args.use_base:
		cloned.BaseDefinition = src



parser = RegisterConsoleCommand(
	"clone_bal",
	handler,
	splitter=obj_name_splitter,
	description=(
		"Clones a Weapon Balance including the part lists."
	)
)
parser.add_argument("base", help="The WeaponBalanceDefinition to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
parser.add_argument(
	"-x", "--suppress-exists",
	action="store_true",
	help="Suppress the error message when an object already exists."
)
parser.add_argument(
	"-b", "--use-base",
	action="store_true",
	help="Uses the base definition of the original object rather than setting the original object as the base."
)