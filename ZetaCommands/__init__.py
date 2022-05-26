import unrealsdk
from Mods.ModMenu import ModPriorities, ModTypes, RegisterMod, SDKMod
import Mods
from typing import Dict

VersionMajor: int = 1
VersionMinor: int = 0

from . import builtins

class ZetaCommands(SDKMod):
    Name: str = "Zeta's Commands"
    Author: str = "ZetaDaemon"
    Description: str = (
        "Adds a few more console commands onto Command Extentions."
    )
    Version: str = f"{VersionMajor}.{VersionMinor}"

    Types: ModTypes = ModTypes.Library
    Priority = ModPriorities.Library

    Status: str = "<font color=\"#00FF00\">Loaded</font>"
    SettingsInputs: Dict[str, str] = {}


RegisterMod(ZetaCommands())