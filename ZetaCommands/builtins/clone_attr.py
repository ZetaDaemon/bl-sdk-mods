import unrealsdk
import argparse
import functools
from typing import Callable, Dict

from Mods.CommandExtensions import RegisterConsoleCommand
from Mods.CommandExtensions.builtins import is_obj_instance, obj_name_splitter, parse_object
from Mods.CommandExtensions.builtins.clone import clone_object, parse_clone_target

contextresolverchain = "ContextResolverChain"
valueresolverchain = "ValueResolverChain"

def object_to_clone(base: unrealsdk.UObject, flag: bool):
	if flag:
		return base.ObjectArchetype
	else:
		return base

def handle_ResolverChain(base: unrealsdk.UObject, clone: unrealsdk.UObject, ResolverChainName: str, flag: bool):
	ResolverChain = getattr(base, ResolverChainName)
	cloned_ResolverChain = []
	for Resolver in ResolverChain:
		clonedResolver = clone_object(object_to_clone(Resolver, flag), clone, Resolver.Class.Name)
		cloned_ResolverChain.append(clonedResolver)
		#unrealsdk.Log(cloned_ResolverChain)
	setattr(clone, ResolverChainName, cloned_ResolverChain) 


def handler(args: argparse.Namespace) -> None:
	src = parse_object(args.base)
	if src is None:
		return
	if not is_obj_instance(src, "AttributeDefinition"):
		unrealsdk.Log(f"Object {src.PathName(src)} must be a 'AttributeDefinition'!")
		return

	outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
	if name is None:
		return
	cloned = clone_object(object_to_clone(src, args.use_default), outer, name)

	handle_ResolverChain(src, cloned, contextresolverchain, args.use_default)
	handle_ResolverChain(src, cloned, valueresolverchain, args.use_default)



parser = RegisterConsoleCommand(
	"clone_attr",
	handler,
	splitter=obj_name_splitter,
	description=(
		"Clones an attribute as well as the resolver chains."
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
	"-d", "--use-default",
	action="store_true",
	help="Uses the ObjectArchetype of the base attribute to create the clone rather than the base attribute itself"
)