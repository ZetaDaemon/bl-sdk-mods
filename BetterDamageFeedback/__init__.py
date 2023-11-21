import unrealsdk
from Mods.ModMenu import (
    ModTypes,
    RegisterMod,
    SDKMod,
    EnabledSaveType,
    Game,
    OptionManager,
    Hook,
    Mods,
    SettingsManager,
)
from Mods.Structs import PlayerRecentDamageEventData
from Mods.Enums import EDamageSurfaceType
from dataclasses import dataclass
from typing import Any, List, Tuple, Dict, Union
import json
from os import path

try:
    from Mods import CommandExtensions
except ImportError:
    CommandExtensions = None
if CommandExtensions is not None:
    import argparse
    from Mods.CommandExtensions import RegisterConsoleCommand, UnregisterConsoleCommand
    from Mods.CommandExtensions.builtins import (
        is_obj_instance,
        obj_name_splitter,
        parse_object,
    )


dir_path = path.dirname(path.realpath(__file__))


def clamp(value, minv, maxv):
    return max(min(value, maxv), minv)


def Vector(vector):
    return (vector.X, vector.Y, vector.Z)


def Rotator(rotator):
    return (rotator.Pitch, rotator.Yaw, rotator.Roll)


class SubHeading(OptionManager.Options.Field):
    def __init__(
        self, Caption: str, Description: str = "", *, IsHidden: bool = True
    ) -> None:
        self.Caption = Caption
        self.Description = Description
        self.IsHidden = IsHidden
        return


class Location:
    x: int = 0
    y: int = 0
    z: int = 0

    def __init__(self, x=0, y=0, z=0, *, vector=None) -> None:
        if vector is not None:
            self.x = vector.X
            self.y = vector.Y
            self.z = vector.Z
            return
        self.x = x
        self.y = y
        self.z = z

    def get(self):
        return (self.x, self.y, self.z)

    def __repr__(self) -> str:
        return f"{self.get()}"


@dataclass
class RecentDamage:
    damage_dealt: int = 0
    damage_type: unrealsdk.UObject = None
    location: Location = None
    time: int = 0
    surface: EDamageSurfaceType = EDamageSurfaceType.DMGSURFACE_Generic
    crit: bool = False
    resisted: bool = False
    healing: bool = False

    def __post_init__(self):
        if self.location is None:
            self.location = Location()


hide_damage_number_option = OptionManager.Options.Boolean(
    Caption="Hide Damage Number",
    Description="Disable damage numbers from showing.",
    StartingValue=False,
)
crit_option = OptionManager.Options.Boolean(
    Caption="Crit Particle",
    Description="Enable 'CRITICAL' particle effect.",
    StartingValue=True,
)
crit_colour_option = OptionManager.Options.Boolean(
    Caption="Coloured Crits",
    Description="Enable critical hit number colour shifting.",
    StartingValue=True,
)
crit_size_option = OptionManager.Options.Boolean(
    Caption="Larger Crits",
    Description="Enable larger critical hit numbers.",
    StartingValue=True,
)
hit_sound_option = OptionManager.Options.Boolean(
    Caption="Hit Sounds",
    Description="Play a sound when hitting enemies based on the health type hit.",
    StartingValue=True,
)
crit_sound_option = OptionManager.Options.Boolean(
    Caption="Crit Sound",
    Description="Play a sound when landing a critical hit.",
    StartingValue=True,
)
crit_sound_selection = OptionManager.Options.Spinner(
    Caption="Crit Sound Effect",
    Description="Sound to play on landing a critical hit",
    StartingValue="Ding",
    Choices=["Ding", "Arcade", "Click"],
)
sound_location_option = OptionManager.Options.Boolean(
    Caption="Play Sounds From Player",
    Description="Play damage sounds from the player instead of from where you hit, disabling volume dropoff with distance.",
    StartingValue=False,
)
damage_colours_option = OptionManager.Options.Nested(
    Caption="Damage Colours",
    Description="Adjust the colours for each damage type",
    Children=list(),
)


def gen_damage_colour_option(
    element: str,
    red: int,
    green: int,
    blue: int,
    crit_red: int,
    crit_green: int,
    crit_blue: int,
) -> OptionManager.Options.Nested:
    new_colour_option = OptionManager.Options.Nested(
        Caption=element,
        Description=f"Set the colours for {element}",
        Children=list(),
    )
    r_option = OptionManager.Options.Slider(
        Caption="Red",
        Description="Red Value",
        StartingValue=red,
        MinValue=0,
        MaxValue=100,
        Increment=1,
    )
    g_option = OptionManager.Options.Slider(
        Caption="Green",
        Description="Green Value",
        StartingValue=green,
        MinValue=0,
        MaxValue=100,
        Increment=1,
    )
    b_option = OptionManager.Options.Slider(
        Caption="Blue",
        Description="Blue Value",
        StartingValue=blue,
        MinValue=0,
        MaxValue=100,
        Increment=1,
    )
    crit_r_option = OptionManager.Options.Slider(
        Caption="Crit Red",
        Description="Crit Red Value",
        StartingValue=crit_red,
        MinValue=0,
        MaxValue=100,
        Increment=1,
    )
    crit_g_option = OptionManager.Options.Slider(
        Caption="Crit Green",
        Description="Crit Green Value",
        StartingValue=crit_green,
        MinValue=0,
        MaxValue=100,
        Increment=1,
    )
    crit_b_option = OptionManager.Options.Slider(
        Caption="Crit Blue",
        Description="Crit Blue Value",
        StartingValue=crit_blue,
        MinValue=0,
        MaxValue=100,
        Increment=1,
    )
    new_colour_option.Children = [
        r_option,
        g_option,
        b_option,
        crit_r_option,
        crit_g_option,
        crit_b_option,
    ]
    damage_colours_option.Children.append(new_colour_option)
    return new_colour_option


damage_type_colour_dict: Dict[
    unrealsdk.UObject,
    Tuple[
        Tuple[
            OptionManager.Options.Slider,
            OptionManager.Options.Slider,
            OptionManager.Options.Slider,
        ],
        Tuple[
            OptionManager.Options.Slider,
            OptionManager.Options.Slider,
            OptionManager.Options.Slider,
        ],
    ],
] = {}

default_damage_colours: Dict[
    str,
    Dict[str, Union[Tuple[int, int, int], Union[OptionManager.Options.Nested, None]]],
] = {
    "Normal": {"Body": (70, 70, 70), "Crit": (100, 35, 35), "Option": None},
    "Explosive": {"Body": (50, 50, 0), "Crit": (100, 100, 0), "Option": None},
    "Fire": {"Body": (80, 20, 0), "Crit": (100, 50, 0), "Option": None},
    "Shock": {"Body": (0, 15, 80), "Crit": (0, 40, 100), "Option": None},
    "Corrosive": {"Body": (0, 70, 0), "Crit": (40, 100, 0), "Option": None},
    "Slag": {"Body": (15, 0, 80), "Crit": (40, 0, 100), "Option": None},
}
settings_path = f"{dir_path}/settings.json"
if path.isfile(settings_path):
    with open(settings_path) as file:
        settings_json = json.load(file)
        for element, data in settings_json["Options"]["Damage Colours"].items():
            if element in default_damage_colours:
                continue
            default_damage_colours[element] = {
                "Body": (data["Red"], data["Green"], data["Blue"]),
                "Crit": (data["Crit Red"], data["Crit Green"], data["Crit Blue"]),
                "Option": None,
            }
colour_name_damage_types: Dict[str, List[str]] = {
    "Normal": ["GD_Impact.DamageType.DmgType_Normal"],
    "Explosive": [
        "GD_Explosive.DamageType.DmgType_Explosive_Impact",
        "GD_Explosive.DamageType.DmgType_Explosive_Impact_ForceFlinch",
        "GD_Explosive.DamageType.DmgType_Explosive_Impact_Friendly",
    ],
    "Fire": [
        "GD_Incendiary.DamageType.DmgType_Incendiary_Impact",
        "GD_Incendiary.DamageType.DmgType_Incendiary_Impact_NoDoT",
        "GD_Incendiary.DamageType.DmgType_Incendiary_Status",
    ],
    "Shock": [
        "GD_Shock.DamageType.DmgType_Shock_Impact",
        "GD_Shock.DamageType.DmgType_Shock_Impact_NoDoT",
        "GD_Shock.DamageType.DmgType_Shock_Status",
    ],
    "Corrosive": [
        "GD_Corrosive.DamageType.DmgType_Corrosive_Impact",
        "GD_Corrosive.DamageType.DmgType_Corrosive_Impact_NoDoT",
        "GD_Corrosive.DamageType.DmgType_Corrosive_Status",
    ],
    "Slag": [
        "GD_Amp.DamageType.DmgType_Amp_Impact",
        "GD_Amp.DamageType.DmgType_Amp_Status",
    ],
}


hit_sound_names: Dict[EDamageSurfaceType, str] = {
    EDamageSurfaceType.DMGSURFACE_Generic: "Ake_Imp_Bullets.Ak_Play_Imp_Bullets",
    EDamageSurfaceType.DMGSURFACE_Flesh: "Ake_Imp_Bullets.Ak_Play_Imp_Bullets",
    EDamageSurfaceType.DMGSURFACE_Armor: "Ake_Imp_Bullets.Ak_Play_Imp_Bullets",
    EDamageSurfaceType.DMGSURFACE_Shield: "Ake_Imp_Bullets.Ak_Play_Imp_Bullets",
}
hit_sounds: Dict[EDamageSurfaceType, unrealsdk.UObject] = {}

crit_sound_names: Dict[str, str] = {
    "Ding": "Ake_UI.UI_Generic.Ak_Play_UI_Generic_InGame_Close",
    "Arcade": "Ake_UI.UI_HUD.Ak_Play_UI_HUD_Token_Unlocked",
    "Click": "Ake_UI.UI_Generic.Ak_Play_UI_Generic_InGame_Select",
}
crit_sounds: Dict[str, unrealsdk.UObject] = {}


willow_globals: unrealsdk.UObject = None
sound_manager: unrealsdk.UObject = None

# For use if mods want to override the regular damage number tracking system and provide their own.
use_custom_data_input: bool = False


def play_damage_sound(
    PC: unrealsdk.UObject,
    damage_location: Tuple[int, int, int],
    surface: EDamageSurfaceType,
    was_crit: bool,
):
    sound = hit_sounds[surface]
    location = (
        Vector(PC.Pawn.Location)
        if sound_location_option.CurrentValue
        else damage_location
    )
    if crit_sound_option.CurrentValue and was_crit:
        sound_manager.StaticPlayWorldAkEvent(
            crit_sounds[crit_sound_selection.CurrentValue],
            location,
        )
    if hit_sound_option.CurrentValue:
        sound_manager.StaticPlayWorldAkEvent(
            sound,
            location,
        )


def display_damage_event(event: RecentDamage, PC: unrealsdk.UObject):
    damage = event.damage_dealt
    if damage <= 0.00010:
        return
    globals_def = willow_globals.GetWillowGlobals().GetGlobalsDefinition()
    event_location = event.location.get()

    if "Status" not in PC.PathName(event.damage_type):
        play_damage_sound(PC, event_location, event.surface, event.crit)

    if hide_damage_number_option.CurrentValue:
        return

    particle_rotation = Rotator(PC.Rotation)
    particles = PC.WorldInfo.MyEmitterPool.SpawnEmitter(
        globals_def.DamageDisplayParticles,
        event_location,
        particle_rotation,
    )
    if event.damage_type is None:
        display_colour = (0.7, 0.7, 0.7)
    elif event.damage_type not in damage_type_colour_dict:
        standard_colour = (
            event.damage_type.DamageColor.R,
            event.damage_type.DamageColor.G,
            event.damage_type.DamageColor.B,
        )
        crit_colour = standard_colour
    else:
        standard_colour, crit_colour = damage_type_colour_dict[event.damage_type]
        if crit_colour_option.CurrentValue and event.crit:
            display_colour = crit_colour
        else:
            display_colour = standard_colour
        display_colour = tuple(x.CurrentValue / 100 for x in display_colour)

    if damage > globals_def.DamageDisplayShortenDamageThreshold:
        damage_shorten_param = 1
        damage *= globals_def.DamageDisplayShortenDamageMultiplyBy
    else:
        damage_shorten_param = 0
    particles.SetFloatParameter(
        globals_def.DamageDisplayShortenParamName, damage_shorten_param
    )

    particles.SetVectorParameter(
        globals_def.DamageDisplayParticleColorParamName, display_colour
    )
    particles.SetFloatParameter(
        globals_def.DamageDisplayParticleDamageParamName, damage
    )

    min_dist = globals_def.DamageDisplayParticleSizeMinDist**2
    max_dist = globals_def.DamageDisplayParticleSizeMaxDist**2
    pc_view_location = Vector(PC.ViewTarget.Location)
    location_difference = tuple(l - r for l, r in zip(pc_view_location, event_location))
    location_difference_sq = sum([x**2 for x in location_difference])
    size = clamp((location_difference_sq - min_dist) / max_dist, 0.0, 1.0)
    if crit_size_option.CurrentValue:
        size = 1.5 * size + 0.1 if event.crit else size
    particles.SetVectorParameter(
        globals_def.DamageDisplayParticleSizeParamName, (size, size, size)
    )

    crit_val = (
        globals_def.DamageDisplayParticleCriticalHitParamValue
        if event.crit and crit_option.CurrentValue
        else 0
    )

    damage_id = (
        0 if event.damage_type is None else int(event.damage_type.DamageLanguageId)
    )
    crit_param = {
        0: globals_def.DamageDisplayParticleCriticalHitParamName,
        1: globals_def.DamageDisplayParticleCriticalHitParamNameEs,
        2: globals_def.DamageDisplayParticleCriticalHitParamNameFr,
        3: globals_def.DamageDisplayParticleCriticalHitParamNameIt,
        4: globals_def.DamageDisplayParticleCriticalHitParamNameDe,
    }[damage_id]
    particles.SetFloatParameter(crit_param, crit_val)

    particles.SetFloatParameter(
        globals_def.DamageDisplayParticleHealingParamName,
        globals_def.DamageDisplayParticleHealingParamValue if event.healing else 0,
    )

    particles.SetFloatParameter(
        globals_def.DamageDisplayParticleResistParamName,
        globals_def.DamageDisplayParticleResistParamValue if event.resisted else 0,
    )
    particles.SetVectorParameter(
        globals_def.DamageDisplayParticleResistColorParamName, display_colour
    )

    particles.TranslucencySortPriority = globals_def.DamageDisplaySortPriority
    particles.ForceUpdate(False)


VERSION_MAJOR = 1
VERSION_MINOR = 1


class BetterDamageFeedback(SDKMod):
    Name: str = "Better Damage Feedback"
    Author: str = "ZetaDaemon"
    Description: str = "Enhances damage numbers and feedback from damaging enemies."
    Version: str = f"v{VERSION_MAJOR}.{VERSION_MINOR}"
    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadOnMainMenu
    Options: List[OptionManager.Options.Base] = [
        damage_colours_option,
        hide_damage_number_option,
        crit_option,
        crit_colour_option,
        crit_size_option,
        hit_sound_option,
        crit_sound_option,
        crit_sound_selection,
        sound_location_option,
    ]

    def ModOptionChanged(
        self, option: OptionManager.Options.Base, new_value: Any
    ) -> None:
        if option != crit_sound_selection or self.Status != "Enabled":
            return
        sound_manager.StaticPlayUIAkEvent(crit_sounds[new_value])

    @Hook("WillowGame.WillowDamageTypeDefinition.DisplayRecentDamageForPlayer")
    def display_damage(
        self,
        this: unrealsdk.UObject,
        function: unrealsdk.UFunction,
        params: unrealsdk.FStruct,
    ) -> bool:
        if use_custom_data_input:
            return False
        damage_event_data = PlayerRecentDamageEventData(params.DamageEventData)
        surface = EDamageSurfaceType.DMGSURFACE_Flesh
        if damage_event_data.DamagedActor.RecentDamage.ShieldDamage > 0.00010:
            surface = EDamageSurfaceType.DMGSURFACE_Shield
        elif damage_event_data.DamagedActor.IsFullyArmored():
            surface = EDamageSurfaceType.DMGSURFACE_Armor
        event = RecentDamage(
            damage_event_data.TotalDamageForDamageType,
            damage_event_data.DamageTypeDefinition,
            Location(vector=damage_event_data.DamageLocation),
            damage_event_data.DamageTime,
            surface,
            damage_event_data.DamageEventFlags & 1 == 1,
            damage_event_data.DamageEventFlags & 4 == 1,
            damage_event_data.DamageEventFlags & 2 == 1,
        )
        display_damage_event(event, params.PC)
        return False

    def find_objects(self):
        global willow_globals, sound_manager, crit_sounds
        willow_globals = unrealsdk.FindObject(
            "WillowGlobals", "WillowGame.Default__WillowGlobals"
        )
        sound_manager = unrealsdk.FindObject(
            "WorldSoundManager", "Engine.Default__WorldSoundManager"
        )
        for key, value in crit_sound_names.items():
            crit_sounds[key] = unrealsdk.FindObject("AkEvent", value)

        for key, value in hit_sound_names.items():
            hit_sounds[key] = unrealsdk.FindObject("AkEvent", value)

        obj = unrealsdk.FindObject(
            "DistributionVectorParticleParameter",
            "FX_CHAR_Damage_Matrix.Particles.Part_Dynamic_Number:ParticleModuleSizeScale_9.DistributionVectorParticleParameter_0",
        )
        obj.MaxInput = (10, 10, 10)
        obj.MaxOutput = (10, 10, 10)

        for name, damage_types in colour_name_damage_types.items():
            red, green, blue = default_damage_colours[name]["Body"]
            crit_red, crit_green, crit_blue = default_damage_colours[name]["Crit"]
            colour_option = gen_damage_colour_option(
                name, red, green, blue, crit_red, crit_green, crit_blue
            )
            default_damage_colours[name]["Option"] = colour_option
            for damage_type in damage_types:
                obj = unrealsdk.FindObject("WillowDamageTypeDefinition", damage_type)
                damage_type_colour_dict[obj] = (
                    (
                        colour_option.Children[0],
                        colour_option.Children[1],
                        colour_option.Children[2],
                    ),
                    (
                        colour_option.Children[3],
                        colour_option.Children[4],
                        colour_option.Children[5],
                    ),
                )

    if CommandExtensions is not None:
        try:
            UnregisterConsoleCommand("add_element")
        except KeyError:
            pass
        try:
            UnregisterConsoleCommand("add_damage_type")
        except KeyError:
            pass

        def add_element_handler(args: argparse.Namespace) -> None:
            if args.element in default_damage_colours:
                if not args.suppress_exists:
                    unrealsdk.Log(f"{args.element} is already a registered element")
                return
            if len(args.colour) != 3:
                unrealsdk.Log(
                    "'colour' must have 3 integer args in the format of 'r, g, b'"
                )
                return
            if len(args.crit) != 3:
                unrealsdk.Log("'crit' must have 3 args in the format of 'r, g, b'")
                return
            try:
                red, green, blue = tuple(int(x) for x in args.colour)
            except ValueError:
                unrealsdk.Log(
                    "'colour' must have 3 integer args in the format of 'r, g, b'"
                )
                return
            try:
                crit_red, crit_green, crit_blue = tuple(int(x) for x in args.crit)
            except ValueError:
                unrealsdk.Log(
                    "'crit' must have 3 integer args in the format of 'r, g, b'"
                )
                return
            if damage_type_colour_dict == {}:
                colour_option = None
            else:
                colour_option = gen_damage_colour_option(
                    args.element, red, green, blue, crit_red, crit_green, crit_blue
                )
            default_damage_colours[args.element] = {
                "Body": (red, green, blue),
                "Crit": (crit_red, crit_green, crit_blue),
                "Option": colour_option,
            }

        element_parser = RegisterConsoleCommand(
            "add_element",
            add_element_handler,
            splitter=obj_name_splitter,
            description=("Adds a damage type as an option for customisation."),
        )
        element_parser.add_argument(
            "element",
            help="The name of the element, used to group multiple damage types together under one colour.",
        )
        element_parser.add_argument(
            "colour",
            nargs=3,
            help=(
                "The colour for regular hits, in 'r g b' format."
                " Values must be between 1-100 due to settings display limitations, are later divided by 100 to create the actual colour",
            ),
        )
        element_parser.add_argument(
            "crit",
            nargs=3,
            help=(
                "The colour for critical hits, in 'r g b' format."
                " Values must be between 1-100 due to settings display limitations, are later divided by 100 to create the actual colour",
            ),
        )
        element_parser.add_argument(
            "-x",
            "--suppress-exists",
            action="store_true",
            help="Suppress the error message when an object already exists.",
        )

        def add_damage_type_handler(args: argparse.Namespace) -> None:
            damage_type = parse_object(args.type)
            if damage_type is None:
                return
            if not is_obj_instance(damage_type, "WillowDamageTypeDefinition"):
                unrealsdk.Log(f"type {damage_type} is not a WillowDamageTypeDefinition")
                return
            if damage_type in damage_type_colour_dict:
                if not args.suppress_exists:
                    unrealsdk.Log(f"{damage_type} is already a registered damage type")
                return
            element = args.element
            if element not in default_damage_colours:
                unrealsdk.Log(f"element {element} is not a registered element")
                return
            if (
                damage_type_colour_dict == {}
                or default_damage_colours[element]["Option"] is None
            ):
                if element in colour_name_damage_types:
                    colour_name_damage_types[element].append(args.type)
                else:
                    colour_name_damage_types[element] = [args.type]
                return
            colour_option = default_damage_colours[element]["Option"]
            damage_type_colour_dict[damage_type] = (
                (
                    colour_option.Children[0],
                    colour_option.Children[1],
                    colour_option.Children[2],
                ),
                (
                    colour_option.Children[3],
                    colour_option.Children[4],
                    colour_option.Children[5],
                ),
            )

        type_parser = RegisterConsoleCommand(
            "add_damage_type",
            add_damage_type_handler,
            splitter=obj_name_splitter,
            description=("Adds a damage type as an option for customisation."),
        )
        type_parser.add_argument("type", help="The DamageType.")
        type_parser.add_argument(
            "element",
            help="The name of the element, used to group multiple damage types together under one colour.",
        )
        type_parser.add_argument(
            "-x",
            "--suppress-exists",
            action="store_true",
            help="Suppress the error message when an object already exists.",
        )

    def Enable(self) -> None:
        self.find_objects()
        super().Enable()


instance = BetterDamageFeedback()
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)
