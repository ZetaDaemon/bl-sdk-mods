import unrealsdk
from Mods.ModMenu import ModTypes, RegisterMod, SDKMod, Game, Options, EnabledSaveType
from Mods.Structs import WeaponDefinitionData, AppliedAttributeEffect, ItemDefinitionData
from random import choice
from typing import Dict

EWeaponType = [
    'WT_Pistol',
    'WT_Shotgun',
    'WT_SMG',
    'WT_SniperRifle',
    'WT_AssaultRifle',
    'WT_RocketLauncher'
]

WeaponCustomPartTypeData = [
    'BodyPartData',
    'GripPartData',
    'BarrelPartData',
    'SightPartData',
    'StockPartData',
    'ElementalPartData',
    'Accessory1PartData',
    'Accessory2PartData',
    'MaterialPartData'
]

class GearRandomiser(SDKMod):
    Name: str = "Gear Randomiser"
    Author: str = "ZetaDaemon"
    Description: str = "Randomises all gear in the game.\nGives option to set class mod usability via settings.\n\nIf using with a mod that adds new items make sure to re-cache parts after the other mod is enabled."
    Version: str = "1.0"
    SupportedGames = Game.BL2
    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadOnMainMenu

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "R": "Update Parts",
    }

    SavedComCharacters: Dict[str, str] = {}

    AllWeaponParts = []
    AllWeaponMaterials = []
    WeaponParts = {
        'BodyPartData': {
            "WT_Pistol": [],
            "WT_Shotgun": [],
            "WT_SMG": [],
            "WT_SniperRifle": [],
            "WT_AssaultRifle": [],
            "WT_RocketLauncher": [],
        },
        'GripPartData': [],
        'BarrelPartData': [],
        'SightPartData': [],
        'StockPartData': [],
        'ElementalPartData': [],
        'Accessory1PartData': [],
        'Accessory2PartData': [],
        'MaterialPartData': {
            "WT_Pistol": [],
            "WT_Shotgun": [],
            "WT_SMG": [],
            "WT_SniperRifle": [],
            "WT_AssaultRifle": [],
            "WT_RocketLauncher": [],
        }
    }

    ShieldParts = []
    ShieldAccessoryParts = []
    ShieldMaterialParts = []

    GrenadeParts = []
    GrenadePayloadParts = []
    GrenadeMaterialParts = []

    ClassModParts = []
    
    RelicParts = []

    def SettingsInputPressed(self, action: str) -> None:
        if action == "Update Parts":
            self.ResetComs()
            self.CacheParts()
        else:
            super().SettingsInputPressed(action)

    def __init__(self) -> None:
        self.ChaosMode = Options.Boolean (
            Caption = "Chaos Mode",
            Description = "Randomises all parts on a gun with no restriction as to what goes where",
            StartingValue = False,
            Choices = ("Off", "On"),
            IsHidden = False
        )

        self.ComUsability = Options.Boolean (
            Caption = "COM Usability",
            Description = "Enables the option to set the player class for class mods",
            StartingValue = False,
            Choices = ("Off", "On"),
            IsHidden = False
        )

        self.ComCharacter = Options.Spinner (
            Caption="Classmod Character",
            Description="Set the character class for class mods",
            StartingValue = "Axton",
            Choices = ["Axton", "Gaige", "Krieg", "Maya", "Salvador", "Zero"],
            IsHidden = False
        )
        self.Options = [
            self.ChaosMode,
            self.ComUsability,
            self.ComCharacter
        ]

    
    def ResetComs(self):
        for COM, Class in self.SavedComCharacters.items():
            unrealsdk.FindObject("ClassModDefinition", COM).RequiredPlayerClass = unrealsdk.FindObject("PlayerClassIdentifierDefinition", Class)
    
    def ModOptionChanged(self, option, newValue) -> None:
        if option == self.ComCharacter:
            if self.ComUsability.CurrentValue:
                char = self.PlayerClasses[newValue]
                for COM in unrealsdk.FindAll("ClassModDefinition"):
                    COM.RequiredPlayerClass = char
        
        if option == self.ComUsability:
            if not newValue:
                self.ResetComs()
            else:
                char = self.PlayerClasses[self.ComCharacter.CurrentValue]
                for COM in unrealsdk.FindAll("ClassModDefinition"):
                    COM.RequiredPlayerClass = char
    
    def CacheParts(self):
        self.AllWeaponParts = []
        self.AllWeaponMaterials = []
        self.WeaponParts = {
            'BodyPartData': {
                "WT_Pistol": [],
                "WT_Shotgun": [],
                "WT_SMG": [],
                "WT_SniperRifle": [],
                "WT_AssaultRifle": [],
                "WT_RocketLauncher": [],
            },
            'GripPartData': [],
            'BarrelPartData': [],
            'SightPartData': [],
            'StockPartData': [],
            'ElementalPartData': [],
            'Accessory1PartData': [],
            'Accessory2PartData': [],
            'MaterialPartData': {
                "WT_Pistol": [],
                "WT_Shotgun": [],
                "WT_SMG": [],
                "WT_SniperRifle": [],
                "WT_AssaultRifle": [],
                "WT_RocketLauncher": [],
            }
        }

        self.ShieldParts = []
        self.ShieldAccessoryParts = []
        self.ShieldMaterialParts = []

        self.GrenadeParts = []
        self.GrenadePayloadParts = []
        self.GrenadeMaterialParts = []

        self.ClassModParts = []

        self.RelicParts = []

        for PartList in unrealsdk.FindAll("WeaponPartListCollectionDefinition"):
            for PartData in WeaponCustomPartTypeData:
                for WeightedPart in getattr(PartList, PartData).WeightedParts:
                    Part = WeightedPart.Part
                    if Part is None:
                        continue
                    PartName = Part.PathName(Part)
                    if PartData == "MaterialPartData":
                        if PartName not in self.AllWeaponMaterials:
                            self.AllWeaponMaterials.append(PartName)
                    else:
                        if PartName not in self.AllWeaponParts:
                            self.AllWeaponParts.append(PartName)
                    if not (PartData == "MaterialPartData" or PartData == "BodyPartData"):
                        if PartName not in self.WeaponParts[PartData]:
                            self.WeaponParts[PartData].append(PartName)
                        continue
                    if PartList.AssociatedWeaponType is None:
                        continue
                    WeaponType = EWeaponType[PartList.AssociatedWeaponType.WeaponType]
                    if PartName not in self.WeaponParts[PartData][WeaponType]:
                        self.WeaponParts[PartData][WeaponType].append(PartName)
                    if PartName not in self.AllWeaponParts:
                        self.AllWeaponParts.append(PartName)

        for part in unrealsdk.FindAll("ShieldPartDefinition"):
            name = part.PathName(part)
            if "accessory" in name.lower():
                self.ShieldAccessoryParts.append(name)
                continue
            if "material" in name.lower():
                self.ShieldMaterialParts.append(name)
                continue
            self.ShieldParts.append(name)

        for part in unrealsdk.FindAll("GrenadeModPartDefinition"):
            name = part.PathName(part)
            if "payload" in name.lower():
                self.GrenadePayloadParts.append(name)
                continue
            if "material" in name.lower():
                self.GrenadeMaterialParts.append(name)
                continue
            self.GrenadeParts.append(name)

        for part in unrealsdk.FindAll("ClassModPartDefinition"):
            self.ClassModParts.append(part.PathName(part))

        for part in unrealsdk.FindAll("ArtifactPartDefinition"):
            self.RelicParts.append(part.PathName(part))
        
        for COM in unrealsdk.FindAll("ClassModDefinition"):
            self.SavedComCharacters[COM.PathName(COM)] = COM.PathName(COM.RequiredPlayerClass)

        if self.ComUsability.CurrentValue:
            char = self.PlayerClasses[self.ComCharacter.CurrentValue]
            for COM in unrealsdk.FindAll("ClassModDefinition"):
                COM.RequiredPlayerClass = char
    
    def RandomiseGunDef(self, DefinitionData):
        if not self.ChaosMode.CurrentValue:
            WeaponType = EWeaponType[DefinitionData.WeaponTypeDefinition.WeaponType]
            DefinitionData.BodyPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.WeaponParts["BodyPartData"][WeaponType]))
            DefinitionData.BarrelPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.WeaponParts["BarrelPartData"]))
            DefinitionData.ElementalPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.WeaponParts["ElementalPartData"]))
            DefinitionData.Accessory1PartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.WeaponParts["Accessory1PartData"] + self.WeaponParts["Accessory1PartData"] + self.WeaponParts["BarrelPartData"]))
            if DefinitionData.BalanceDefinition.RuntimePartListCollection.Accessory2PartData.bEnabled:
                DefinitionData.Accessory2PartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.WeaponParts["Accessory2PartData"]))
            DefinitionData.MaterialPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.WeaponParts["MaterialPartData"][WeaponType]))
        else:
            DefinitionData.BodyPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponParts))
            DefinitionData.GripPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponParts))
            DefinitionData.BarrelPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponParts))
            DefinitionData.SightPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponParts))
            DefinitionData.StockPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponParts))
            DefinitionData.ElementalPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.WeaponParts["ElementalPartData"]))
            DefinitionData.Accessory1PartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponParts))
            DefinitionData.Accessory2PartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponParts))
            DefinitionData.MaterialPartDefinition = unrealsdk.FindObject("WeaponPartDefinition", choice(self.AllWeaponMaterials))
        return tuple(WeaponDefinitionData(DefinitionData))
    
    def RandomiseGun(self, this):
        if this.DefinitionData.WeaponTypeDefinition is None:
            return
        if "GD_Weap" not in this.PathName(this.DefinitionData.WeaponTypeDefinition):
            return
        this.DefinitionData = self.RandomiseGunDef(this.DefinitionData)

        this.CalculatePartDependentWeaponBaseValues()
        this.InitializeAttributeSlots(not this.bSelectRandomPartsOnInitialization)
        this.ApplyAllWeaponAttributeEffects(not this.bSelectRandomPartsOnInitialization)
        this.ChooseRandomNameParts()
        this.InitializeAttributeSlotsForNameParts()
        this.ApplyNamePartWeaponAttributeEffects()
        this.RecomputeNormalizedDamageValues()
        this.ComputeValueOfParts()
        WeaponAttributeModifiers = []
        for WAM in this.WeaponAttributeModifiers:
            WeaponAttributeModifiers.append(AppliedAttributeEffect(WAM))
        this.ApplyInternalSlotEffectModifiers(False, this.DefinitionData.WeaponTypeDefinition.GetAttributeSlotMaxActivated(), tuple(WeaponAttributeModifiers))
        this.CacheWeaponCard()
        this.RecomputeAttributeBaseValues()

        FiringMode = this.GetFiringModeDefinition()
        if FiringMode is not None and FiringMode.ExplosionOverrideDefinition is not None and not FiringMode.ExplosionOverideInstanceDataName == 'None':
            Explosion = FiringMode.ExplosionOverrideDefinition.GetExplosion(this)
            if Explosion is not None:
                this.StoreExplosionInstanceData(Explosion, FiringMode.ExplosionOverideInstanceDataName)
            
        if this.DefinitionData.BarrelPartDefinition is not None:
            if this.DefinitionData.BarrelPartDefinition.MuzzleFlashPSTemplates is not None:
                this.MuzzleFlashPSTemplate = this.DefinitionData.BarrelPartDefinition.MuzzleFlashPSTemplates.GetParticleEffect(this)

        BehaviorKernel = unrealsdk.FindObject("BehaviorKernel", "GearboxFramework.Default__BehaviorKernel")
        ConsumerHandle = BehaviorKernel.RegisterBehaviorConsumer(this)
        for part in WeaponDefinitionData(this.DefinitionData):
            try:
                if part.BehaviorProviderDefinition is not None:
                    BehaviorKernel.IntializeBehaviorProviderForConsumer(ConsumerHandle, part.BehaviorProviderDefinition)
            except:
                pass
    
    def RandomiseShieldDef(self, DefinitionData):
        DefinitionData.AlphaItemPartDefinition = unrealsdk.FindObject("ShieldPartDefinition", choice(self.ShieldParts))
        DefinitionData.BetaItemPartDefinition = unrealsdk.FindObject("ShieldPartDefinition", choice(self.ShieldParts))
        DefinitionData.GammaItemPartDefinition = unrealsdk.FindObject("ShieldPartDefinition", choice(self.ShieldParts))
        DefinitionData.DeltaItemPartDefinition = unrealsdk.FindObject("ShieldPartDefinition", choice(self.ShieldAccessoryParts))
        DefinitionData.MaterialItemPartDefinition = unrealsdk.FindObject("ShieldPartDefinition", choice(self.ShieldMaterialParts))
        return tuple(ItemDefinitionData(DefinitionData))
    
    def RandomiseCOMDef(self, DefinitionData):
        DefinitionData.AlphaItemPartDefinition = unrealsdk.FindObject("ClassModPartDefinition", choice(self.ClassModParts))
        DefinitionData.BetaItemPartDefinition = unrealsdk.FindObject("ClassModPartDefinition", choice(self.ClassModParts))
        DefinitionData.GammaItemPartDefinition = unrealsdk.FindObject("ClassModPartDefinition", choice(self.ClassModParts))
        DefinitionData.MaterialItemPartDefinition = unrealsdk.FindObject("ClassModPartDefinition", choice(self.ClassModParts))
        return tuple(ItemDefinitionData(DefinitionData))

    def RandomiseRelicDef(self, DefinitionData):
        DefinitionData.AlphaItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        DefinitionData.BetaItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        DefinitionData.GammaItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        DefinitionData.DeltaItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        DefinitionData.EpsilonItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        DefinitionData.ZetaItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        DefinitionData.EtaItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        DefinitionData.ThetaItemPartDefinition = unrealsdk.FindObject("ArtifactPartDefinition", choice(self.RelicParts))
        return tuple(ItemDefinitionData(DefinitionData))

    def RandomiseGrenadeDef(self, DefinitionData):
        DefinitionData.AlphaItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadePayloadParts))
        DefinitionData.BetaItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadeParts))
        DefinitionData.GammaItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadeParts))
        DefinitionData.DeltaItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadeParts))
        DefinitionData.EpsilonItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadeParts))
        DefinitionData.ZetaItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadeParts))
        DefinitionData.EtaItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadeParts))
        DefinitionData.MaterialItemPartDefinition = unrealsdk.FindObject("GrenadeModPartDefinition", choice(self.GrenadeMaterialParts))
        return tuple(ItemDefinitionData(DefinitionData))
    
    def RandomiseItem(self, this):
        if "Shield" in this.Class.Name:
            this.DefinitionData = self.RandomiseShieldDef(this.DefinitionData)
        elif "Grenade" in this.Class.Name:
            this.DefinitionData = self.RandomiseGrenadeDef(this.DefinitionData)
        elif "ClassMod" in this.Class.Name:
            this.DefinitionData = self.RandomiseCOMDef(this.DefinitionData)
        elif "Artifact" in this.Class.Name:
            this.DefinitionData = self.RandomiseRelicDef(this.DefinitionData)
        else:
            return

        this.ChooseRandomNameParts()
        this.InitializeAttributeSlotsForNameParts()
        this.ComputeValueOfParts()
        ItemAttributeModifiers = []
        for IAM in this.ItemAttributeModifiers:
            ItemAttributeModifiers.append(AppliedAttributeEffect(IAM))
        this.ApplyInternalSlotEffectModifiers(False, this.DefinitionData.ItemDefinition.GetAttributeSlotMaxActivated(), tuple(ItemAttributeModifiers))
        this.CacheItemCard()
        this.RecomputeAttributeBaseValues()

    def Enable(self):
        self.PlayerClasses = {
            "Axton": unrealsdk.FindObject("PlayerClassIdentifierDefinition", "GD_PlayerClassId.Soldier"),
            "Gaige": unrealsdk.FindObject("PlayerClassIdentifierDefinition", "GD_TulipPackageDef.PlayerClassId.Mechromancer"),
            "Krieg": unrealsdk.FindObject("PlayerClassIdentifierDefinition", "GD_LilacPackageDef.PlayerClassId.Psycho"),
            "Maya": unrealsdk.FindObject("PlayerClassIdentifierDefinition", "GD_PlayerClassId.Siren"),
            "Salvador": unrealsdk.FindObject("PlayerClassIdentifierDefinition", "GD_PlayerClassId.Mercenary"),
            "Zero": unrealsdk.FindObject("PlayerClassIdentifierDefinition", "GD_PlayerClassId.Assassin")
        }

        self.CacheParts()

        def Randomise(this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if this.AdditionalQueryInterfaceSource and "Player" in str(this.AdditionalQueryInterfaceSource.Class):
                return True
            if this.DefinitionData is None:
                return True
            if "Weapon" in this.Class.Name:
                self.RandomiseGun(this)
            elif "Shield" in this.Class.Name:
                self.RandomiseItem(this)
            elif "Grenade" in this.Class.Name:
                self.RandomiseItem(this)
            elif "ClassMod" in this.Class.Name:
                self.RandomiseItem(this)
            elif "Artifact" in this.Class.Name:
                self.RandomiseItem(this)
            return True
        
        def RandomiseMissionReward(this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            PC = this.OwningMovie.GetPC()
            if params.RewardChoice >= 0:
                if this.RewardData.WeaponRewards[params.RewardChoice].WeaponTypeDefinition is not None:
                    PC.ReceiveWeaponReward(
                        this.RewardData.Mission,
                        self.RandomiseGunDef(this.RewardData.WeaponRewards[params.RewardChoice])
                    )
                elif this.RewardData.ItemRewards[params.RewardChoice].ItemDefinition is not None:
                    DefinitionData = this.RewardData.ItemRewards[params.RewardChoice]
                    if "Shield" in DefinitionData.ItemDefinition.Class.Name:
                        DefinitionData = self.RandomiseShieldDef(DefinitionData)
                    elif "Grenade" in DefinitionData.ItemDefinition.Class.Name:
                        DefinitionData = self.RandomiseGrenadeDef(DefinitionData)
                    elif "ClassMod" in DefinitionData.ItemDefinition.Class.Name:
                        DefinitionData = self.RandomiseCOMDef(DefinitionData)
                    elif "Artifact" in DefinitionData.ItemDefinition.Class.Name:
                        DefinitionData = self.RandomiseRelicDef(DefinitionData)
                    else:
                        return True

                    PC.ReceiveItemReward(
                        this.RewardData.Mission, 
                        DefinitionData
                    )
            return False

        unrealsdk.RegisterHook("Engine.WillowInventory.ClientInitializeInventoryFromDefinition", "randomiser", Randomise)
        unrealsdk.RegisterHook("WillowGame.MissionRewardGFxObject.AcceptReward", "randomiser", RandomiseMissionReward)

    def Disable(self):
        unrealsdk.RemoveHook("Engine.WillowInventory.ClientInitializeInventoryFromDefinition", "randomiser")
        unrealsdk.RemoveHook("WillowGame.MissionRewardGFxObject.AcceptReward", "randomiser")
        self.ResetComs()

RegisterMod(GearRandomiser())