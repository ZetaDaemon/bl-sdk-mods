import unrealsdk
import argparse

from Mods.CommandExtensions import RegisterConsoleCommand
from Mods.CommandExtensions.builtins import is_obj_instance, obj_name_splitter, parse_object
from Mods.CommandExtensions.builtins.clone import clone_object, parse_clone_target

def ManufacturerCustomGradeWeightData(data):
    return (data.Manufacturer, data.DefaultWeightIndex)

def PartGradeWeightData(data):
    Part = data.Part
    Manufacturer_List = []
    for Manufacturer in data.Manufacturers:
        Manufacturer_List.append(ManufacturerCustomGradeWeightData(Manufacturer))
    Manufacturers = tuple(Manufacturer_List)
    MinGameStageIndex = data.MinGameStageIndex
    MaxGameStageIndex = data.MaxGameStageIndex
    DefaultWeightIndex = data.DefaultWeightIndex
    return (Part, Manufacturers, MinGameStageIndex, MaxGameStageIndex, DefaultWeightIndex)

def add_part_PartGradeWeightData(part, data):
    return (part, data[1], data[2], data[3], data[4])

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
	if name is None:
		return
	cloned = clone_object(src, outer, name)

	if is_obj_instance(src, "WeaponBalanceDefinition"):
		name = ""
		if src.RuntimePartListCollection.outer is not src:
			outer = src.RuntimePartListCollection.outer
			name = f"{cloned.Name}_"
		else:
			outer = cloned
		cloned_WeaponPartListCollection = clone_object(src.WeaponPartListCollection, outer, f"{name}PartList")
		cloned_RuntimePartListCollection = clone_object(src.RuntimePartListCollection, outer, f"{name}RuntimePartList")

		cloned.WeaponPartListCollection = cloned_WeaponPartListCollection
		cloned.RuntimePartListCollection = cloned_RuntimePartListCollection
		if args.third is not None:
			WeightedPart = PartGradeWeightData(cloned.RuntimePartListCollection.BarrelPartData.WeightedParts[0])
			Cloned_WeightedPart = add_part_PartGradeWeightData(unrealsdk.FindObject(WeightedPart[0].Class.Name , args.third), WeightedPart)
			cloned.RuntimePartListCollection.BarrelPartData.WeightedParts = (Cloned_WeightedPart,)
		if args.fourth is not None:
			WeightedPart = PartGradeWeightData(cloned.RuntimePartListCollection.MaterialPartData.WeightedParts[0])
			Cloned_WeightedPart = add_part_PartGradeWeightData(unrealsdk.FindObject(WeightedPart[0].Class.Name , args.fourth), WeightedPart)
			cloned.RuntimePartListCollection.MaterialPartData.WeightedParts = (Cloned_WeightedPart,)

	elif is_obj_instance(src, "ClassModBalanceDefinition"):
		name = ""
		if src.RuntimePartListCollection.outer is not src:
			outer = src.RuntimePartListCollection.outer
			name = f"{cloned.Name}_"
		else:
			outer = cloned
		cloned_ItemPartListCollection = clone_object(src.ItemPartListCollection, outer, f"{name}PartList")
		cloned_RuntimePartListCollection = clone_object(src.RuntimePartListCollection, outer, f"{name}RuntimePartList")

		cloned.ItemPartListCollection = cloned_ItemPartListCollection
		cloned.RuntimePartListCollection = cloned_RuntimePartListCollection

	elif src.PartListCollection is not None:
		name = ""
		if src.PartListCollection.outer is not src:
			outer = src.PartListCollection.outer
			name = f"{cloned.Name}_"
		else:
			outer = cloned
		cloned_ItemPartListCollectionDefinition = clone_object(src.PartListCollection, outer, f"{name}PartList")
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
parser.add_argument("third", nargs='?', default=None, help="The third optional argument.")
parser.add_argument("fourth", nargs='?', default=None, help="The third optional argument.")
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