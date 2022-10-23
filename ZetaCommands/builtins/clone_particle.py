import unrealsdk
import argparse
import functools
from typing import Dict
from collections import Counter

from Mods.CommandExtensions import RegisterConsoleCommand
from Mods.CommandExtensions.builtins import is_obj_instance, obj_name_splitter, parse_object
from Mods.CommandExtensions.builtins.clone import clone_object, parse_clone_target

ClonesDict = Dict[unrealsdk.UObject, unrealsdk.UObject]

def lod_levels(src, emitter, counter, known_clones):
    new_lods = []
    for idx, lod in enumerate(src.LODLevels):
        new_lod = clone_object(lod.ObjectArchetype, emitter, f"{lod.Class.Name}_{idx}")
        new_lod.RequiredModule = lod.RequiredModule
        new_lod.Level = lod.Level
        new_lod.bEnabled = lod.bEnabled
        new_lod.ConvertedModules = lod.ConvertedModules
        new_lod.RequiredModule = lod.RequiredModule
        new_lod.Modules = lod.Modules
        new_lod.TypeDataModule = lod.TypeDataModule
        new_lod.SpawnModule = lod.SpawnModule
        new_lod.EventGenerator = lod.EventGenerator
        new_lod.SpawnModules = lod.SpawnModules
        new_lod.UpdateModules = lod.UpdateModules
        new_lod.PeakActiveParticles = lod.PeakActiveParticles
        new_lods.append(new_lod)
    emitter.LODLevels = tuple(new_lods)

def emitters(src, particle):
    new_emitters = []
    counter = Counter()
    known_clones: ClonesDict = {}
    for idx, emitter in enumerate(src.Emitters):
        new_emitter = clone_object(emitter.ObjectArchetype, particle, f"{emitter.Class.Name}_{idx}")
        new_emitter.EmitterName = emitter.EmitterName
        lod_levels(emitter, new_emitter, counter, known_clones)
        new_emitters.append(new_emitter)
    particle.Emitters = tuple(new_emitters)


def handler(args: argparse.Namespace) -> None:
    src = parse_object(args.base)
    if src is None:
        return
    outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
    if name is None:
        return
    if is_obj_instance(src, "ParticleSystem"):
        new_particle = clone_object(src.ObjectArchetype, outer, name)
        emitters(src, new_particle)
    else:
        unrealsdk.Log(f"Object {src.PathName(src)} must be a 'ParticleSystem'!")
        return


parser = RegisterConsoleCommand(
    "clone_particle",
    handler,
    splitter=obj_name_splitter,
    description="Creates a clone of an existing particle."
)
parser.add_argument("base", help="The object to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
parser.add_argument(
    "-x", "--suppress-exists",
    action="store_true",
    help="Suppress the error message when an object already exists."
)
