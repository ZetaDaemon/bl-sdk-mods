import unrealsdk
from Mods.ModMenu import RegisterMod, SDKMod, Options, EnabledSaveType, ModTypes
from Mods.Enums import EEffectTarget, EModifierType, EAttributeInitializationRounding
from Mods.Structs import SkillEffectData, AttributeInitializationData
from enum import Enum, auto

class Difficulties(Enum):
    Easy = auto()
    Normal = auto()
    Medium = auto()
    Hard = auto()
    Nightmare = auto()

class Attributes(Enum):
    Armor = auto()
    Movespeed = auto()
    Damage = auto()
    Damage_Offhand = auto()
    Fire_Rate = auto()
    Fire_Rate_Offhand = auto()
    Reload_Speed = auto()
    Reload_Speed_Offhand = auto()
    Melee_Damage = auto()

Difficulty_Dict = {
    "Easy": Difficulties.Easy,
    "Normal": Difficulties.Normal,
    "Medium": Difficulties.Medium,
    "Hard": Difficulties.Hard,
    "Nightmare": Difficulties.Nightmare,
}

def Get_Simple_ValueFormula(AID):
    return (
        True,
        AttributeInitializationData(BaseValueConstant=1.0,BaseValueScaleConstant=1.0),
        AID,
        AttributeInitializationData(BaseValueConstant=1.0,BaseValueScaleConstant=1.0),
        AttributeInitializationData(BaseValueConstant=0.0,BaseValueScaleConstant=1.0)
    )


class DifficultyModes(SDKMod):
    Name: str = "Difficulty Modes"
    Author: str = "ZetaDaemon"
    Description: str = (
        "Replaces BAR with a difficulty mode that can be changed in the options.\n"
        "BAR stats and redeeming BAR tokens is disabled while the mod is active, but BAR needs to be on for the effects of the mod to work.\n"
        "Easy has weaker and less aggressive enemies than vanilla. Normal has no modifiers to play at vanilla balance. Medium, Hard and Nightmare increasingly makes enemies tougher and more aggressive."
    )
    Version: str = "1.0"
    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadOnMainMenu

    BAR_SKILL = None

    BARD_Selected_Difficulty = None

    Difficulty_Scalar = {
        Difficulties.Easy: -0.5,
        Difficulties.Normal: 0,
        Difficulties.Medium: 1,
        Difficulties.Hard: 2,
        Difficulties.Nightmare: 4,
    }

    Attribute_Names = {
        Attributes.Armor: "D_Attributes.GameplayAttributes.BaseArmor",
        Attributes.Movespeed: "D_Attributes.GameplayAttributes.FootSpeed",
        Attributes.Damage: "D_Attributes.Weapon.WeaponDamage",
        Attributes.Damage_Offhand: "D_Attributes.OffHandWeapon.WeaponDamage_Offhand",
        Attributes.Melee_Damage: "D_Attributes.DamageSourceModifiers.InstigatedMeleeDamageModifier",
        Attributes.Fire_Rate: "D_Attributes.Weapon.WeaponFireInterval",
        Attributes.Fire_Rate_Offhand: "D_Attributes.OffHandWeapon.WeaponFireInterval_Offhand",
        Attributes.Reload_Speed: "D_Attributes.Weapon.WeaponReloadSpeed",
        Attributes.Reload_Speed_Offhand: "D_Attributes.OffHandWeapon.WeaponReloadSpeed_Offhand",
    }

    Attribute_Objects = {
        Attributes.Armor: None,
        Attributes.Movespeed: None,
        Attributes.Damage: None,
        Attributes.Damage_Offhand: None,
        Attributes.Melee_Damage: None,
        Attributes.Fire_Rate: None,
        Attributes.Fire_Rate_Offhand: None,
        Attributes.Reload_Speed: None,
        Attributes.Reload_Speed_Offhand: None,
    }

    BARD_Names = {
        Attributes.Armor: "GD_Challenges.BadassRewards.BARD_Health_Max",
        Attributes.Movespeed: "GD_Challenges.BadassRewards.BARD_Shield_RechargeRate",
        Attributes.Damage: "GD_Challenges.BadassRewards.BARD_Gun_Damage",
        Attributes.Fire_Rate: "GD_Challenges.BadassRewards.BARD_Gun_FireRate",
        Attributes.Reload_Speed: "GD_Challenges.BadassRewards.BARD_Gun_ReloadSpeed",
    }

    BARD_Label = {
        Attributes.Armor: "Damage Reduction",
        Attributes.Movespeed: "Movement Speed",
        Attributes.Damage: "Damage Dealt",
        Attributes.Fire_Rate: "Fire Rate",
        Attributes.Reload_Speed: "Reload Speed",
    }

    BARD_Objects = {
        Attributes.Armor: None,
        Attributes.Movespeed: None,
        Attributes.Damage: None,
        Attributes.Fire_Rate: None,
        Attributes.Reload_Speed: None,
    }

    Attr_Modifiers = {
        Attributes.Armor: 10.0,
        Attributes.Movespeed: 0.1,
        Attributes.Damage: 0.1,
        Attributes.Damage_Offhand: 0.1,
        Attributes.Melee_Damage: 0.1,
        Attributes.Fire_Rate: -0.2,
        Attributes.Fire_Rate_Offhand: -0.2,
        Attributes.Reload_Speed: -0.2,
        Attributes.Reload_Speed_Offhand: -0.2,
    }

    Saved_Bar_Skill_Effects = None
    Saved_Bar_Presentation_Set = None
    Saved_BARD_Selected_Difficulty_AID = None
    Saved_BARD_Selected_Difficulty_Presentation = None
    Saved_BARD_Objects_Presentation = {
        Attributes.Armor: None,
        Attributes.Movespeed: None,
        Attributes.Damage: None,
        Attributes.Fire_Rate: None,
        Attributes.Reload_Speed: None,
    }
    Saved_BARD_Objects_AID = {
        Attributes.Armor: None,
        Attributes.Movespeed: None,
        Attributes.Damage: None,
        Attributes.Fire_Rate: None,
        Attributes.Reload_Speed: None,
    }
    Saved_BARD_Objects_Labels = {
        Attributes.Armor: None,
        Attributes.Movespeed: None,
        Attributes.Damage: None,
        Attributes.Fire_Rate: None,
        Attributes.Reload_Speed: None,
    }
    

    def __init__(self) -> None:
        self.SelectedDifficulty = Options.Spinner (
            Caption="Difficulty",
            Description="Difficulty mode to play at.",
            StartingValue = "Normal",
            Choices = ["Easy", "Normal", "Medium", "Hard", "Nightmare"],
            IsHidden=False
        )
        self.Options = [
            self.SelectedDifficulty,
        ]
    
    def Setup_Skill(self, selected_difficulty: Difficulties):
        SkillEffectDefinitions = []
        for key, attr in self.Attribute_Objects.items():
            val = self.Attr_Modifiers[key]*self.Difficulty_Scalar[selected_difficulty]
            if key == Attributes.Armor:
                val = (10000/(100-val)) - 100
            SkillEffectDefinitions.append(
                SkillEffectData(
                    AttributeToModify=attr,
                    EffectTarget= EEffectTarget.TARGET_Enemies.value,
                    ModifierType= (EModifierType.MT_PreAdd.value if key == Attributes.Armor else EModifierType.MT_Scale.value),
                    BaseModifierValue= AttributeInitializationData(
                        BaseValueConstant= self.Attr_Modifiers[key]*self.Difficulty_Scalar[selected_difficulty],
                        BaseValueScaleConstant= 1.0
                    )
                )
            )
        self.BAR_SKILL.SkillEffectDefinitions = tuple(SkillEffectDefinitions)

    def Get_Objects(self):
        self.BAR_SKILL = unrealsdk.FindObject("SkillDefinition", "GD_Challenges.BadassSkill.BadassSkill")
        if self.Saved_Bar_Skill_Effects is None:
            sed = []
            for se in self.BAR_SKILL.SkillEffectDefinitions:
                sed.append(SkillEffectData(se))
            self.Saved_Bar_Skill_Effects = tuple(sed)

        for attr, name in self.Attribute_Names.items():
            self.Attribute_Objects[attr] = unrealsdk.FindObject("AttributeDefinition", name)
        
        self.BARD_Selected_Difficulty = unrealsdk.FindObject("BadassRewardDefinition", "GD_Challenges.BadassRewards.BARD_CriticalHitDamage")
        
        gBAR = [self.BARD_Selected_Difficulty]
        for key, name in self.BARD_Names.items():
            self.BARD_Objects[key] = unrealsdk.FindObject("BadassRewardDefinition", name)
            gBAR.append(self.BARD_Objects[key])

        Globals = unrealsdk.FindObject("GlobalsDefinition", "GD_Globals.General.Globals")
        if self.Saved_Bar_Presentation_Set is None:
            self.Saved_Bar_Presentation_Set = []
            for reward in Globals.BadassRewards:
                self.Saved_Bar_Presentation_Set.append(reward)
        Globals.BadassRewards = tuple(gBAR)
    
    def Setup_Presentations(self, selected_difficulty):
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        display_path = PC.PathName(self.BARD_Selected_Difficulty)
        PC.ConsoleCommand(f"set {display_path} RewardString Difficulty: [skill]{selected_difficulty.name}[-skill]")
        if self.Saved_BARD_Selected_Difficulty_AID is None:
            self.Saved_BARD_Selected_Difficulty_AID = self.BARD_Selected_Difficulty.AttrInitDef
        if self.Saved_BARD_Selected_Difficulty_Presentation is None:
            self.Saved_BARD_Selected_Difficulty_Presentation = self.BARD_Selected_Difficulty.Presentation
        self.BARD_Selected_Difficulty.AttrInitDef = None
        self.BARD_Selected_Difficulty.Presentation = None

        for key, obj in self.BARD_Objects.items():
            val = self.Attr_Modifiers[key]*self.Difficulty_Scalar[selected_difficulty]
            if selected_difficulty == Difficulties.Easy:
                if not key == Attributes.Armor:
                    val = val*100 if val < 0 else val*-100
                else:
                    val = val if val < 0 else val*-1
            else:
                if not key == Attributes.Armor:
                    val = val*100 if val > 0 else val*-100
            
            if self.Saved_BARD_Objects_Labels[key] is None:
                self.Saved_BARD_Objects_Labels[key] = obj.RewardString
            if self.Saved_BARD_Objects_Presentation[key] is None:
                self.Saved_BARD_Objects_Presentation[key] = obj.Presentation
            if self.Saved_BARD_Objects_AID[key] is None:
                self.Saved_BARD_Objects_AID[key] = obj.AttrInitDef

            obj.Presentation = None
            obj.AttrInitDef = None
            sign = "+" if val > 0 else ""
            PC.ConsoleCommand(f"set {PC.PathName(obj)} RewardString {self.BARD_Label[key]}: {sign}{round(val)}%")

    def ModOptionChanged(self, option, newValue) -> None:
        selected_difficulty = Difficulty_Dict[newValue]
        self.Setup_Presentations(selected_difficulty)
        self.Setup_Skill(selected_difficulty)

    def Enable(self):
        def buttonstate(this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            this.RedeemButton.SetBool("disabled", True)
            return False
        
        def test(this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            this.BadassRewardsEarned = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
            return True

        selected_difficulty = Difficulty_Dict[self.SelectedDifficulty.CurrentValue]
        self.Get_Objects()
        self.Setup_Presentations(selected_difficulty)
        self.Setup_Skill(selected_difficulty)
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        PC.ConsoleCommand(f"set WillowGame.Default__BadassPanelGFxObject BonusStatsHeader ENEMY STATS")
        unrealsdk.RegisterHook("WillowGame.BadassPanelGFxObject.SetInitialButtonStates","BarButtonState", buttonstate)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.GetBadassRewardsString","BarRewardString", test)

    def Disable(self):
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        barskill = unrealsdk.FindObject("SkillDefinition", "GD_Challenges.BadassSkill.BadassSkill")
        barskill.SkillEffectDefinitions = self.Saved_Bar_Skill_Effects

        self.BARD_Selected_Difficulty.AttrInitDef = self.Saved_BARD_Selected_Difficulty_AID
        self.BARD_Selected_Difficulty.Presentation = self.Saved_BARD_Selected_Difficulty_Presentation
        PC.ConsoleCommand(f"set {PC.PathName(self.BARD_Selected_Difficulty)} RewardString Critical Hit Damage")

        for key, obj in self.BARD_Objects.items():
            obj.Presentation = self.Saved_BARD_Objects_Presentation[key]
            obj.AttrInitDef = self.Saved_BARD_Objects_AID[key]
            PC.ConsoleCommand(f"set {PC.PathName(obj)} RewardString {self.Saved_BARD_Objects_Labels[key]}")

        Globals = unrealsdk.FindObject("GlobalsDefinition", "GD_Globals.General.Globals")
        Globals.BadassRewards = self.Saved_Bar_Presentation_Set

        unrealsdk.RemoveHook("WillowGame.BadassPanelGFxObject.SetInitialButtonStates","BarButtonState")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.GetBadassRewardsString","BarRewardString")

RegisterMod(DifficultyModes())