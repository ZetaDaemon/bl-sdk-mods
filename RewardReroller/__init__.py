import unrealsdk
from Mods.ModMenu import ModTypes, RegisterMod, SDKMod, EnabledSaveType, Mods, Hook
from Mods.ModMenu import ServerMethod, ClientMethod
from Mods.Enums import (
    EInputEvent,
    ECurrencyType,
    EExperienceSource,
    ENetMode,
    EMissionStatus,
    EBackButtonScreen,
)
from Mods.Structs import (
    AttributeInitializationData,
    WeaponDefinitionData,
    ItemDefinitionData,
    PendingMissionRewardData,
)

from random import choice, choices


def is_client():
    return unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode == ENetMode.NM_Client


def is_solo():
    return unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode == ENetMode.NM_Standalone


def get_netmode():
    return unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode


def is_class(obj: unrealsdk.UObject, cls: unrealsdk.UClass) -> bool:
    if obj is None:
        return False
    obj_cls = obj.Class
    while obj_cls:
        if obj_cls == cls:
            return True
        obj_cls = obj_cls.SuperField
    return False


def check_reroll_input(PC: unrealsdk.UObject, ukey: str) -> bool:
    if PC.PlayerInput.bUsingGamepad:
        if ukey == "XboxTypeS_Y":
            return True
    if ukey == PC.PlayerInput.GetKeyForAction("UseSecondary", True):
        return True
    return False


def check_accept_input(ukey: str) -> bool:
    if ukey in ["XboxTypeS_A", "Enter", "XboxTypeS_Start", "LeftMouseButton"]:
        return True
    return False


def get_pc() -> unrealsdk.UObject:
    return unrealsdk.GetEngine().GamePlayers[0].Actor


def get_mission(mission_name: str) -> unrealsdk.UObject:
    return unrealsdk.FindObject("MissionDefinition", mission_name)


class RewardReroller(SDKMod):
    Name: str = "Reward Reroller"
    Author: str = "ZetaDaemon"
    Description: str = (
        "Lets you reroll mission rewards at the cost of eridium.\n"
        "In multiplayer all players will be promted with the mission reward screen to reroll their own items.\n\n"
        "Thankyou to Flare2V and alienoliver for the original work in BL2Fix."
    )
    Version: str = "1.0"
    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    eridiumCost = 2
    PC = None
    default_AID = unrealsdk.FindObject(
        "AttributeInitializationDefinition", "Engine.Default__AttributeInitializationDefinition"
    )
    quest_movie_def = unrealsdk.FindObject(
        "QuestAcceptGFxDefinition", "UI_Mission.MissionInterface_Definition"
    )

    def eval_aid(self, aid: unrealsdk.FStruct):
        return self.default_AID.EvaluateInitializationData(
            tuple(AttributeInitializationData(aid)), get_pc()
        )

    def get_manufacturer(self, balance: unrealsdk.UObject) -> unrealsdk.UObject:
        b = balance
        while len(b.Manufacturers) == 0:
            if b.BaseDefinition is None:
                return None
            b = b.BaseDefinition
        return choice(b.Manufacturers).Manufacturer

    def get_weapon_data(self, balance: unrealsdk.UObject):
        part_list = balance.RuntimePartListCollection
        manufacturer_definition = self.get_manufacturer(balance)
        weapon_type_definition = part_list.AssociatedWeaponType
        return weapon_type_definition, manufacturer_definition

    def get_com_data(self, balance: unrealsdk.UObject):
        b = balance
        while len(b.ClassModDefinitions) == 0:
            if b.BaseDefinition is None:
                return None, None
            b = b.BaseDefinition
        item_definition = choice(b.ClassModDefinitions)

        return item_definition, item_definition.ManufacturerOverride

    def get_item_data(self, balance: unrealsdk.UObject):
        PartList = balance.PartListCollection
        manufacturer_definition = self.get_manufacturer(balance)
        item_definition = balance.InventoryDefinition
        if item_definition is None:
            item_definition = PartList.AssociatedItem
            if item_definition is None:
                return None, None
        return item_definition, manufacturer_definition

    def create_from_balance(self, balance: unrealsdk.UObject, level: int):
        if is_class(balance, unrealsdk.FindClass("WeaponBalanceDefinition")):
            inventory_definition, manufacturer = self.get_weapon_data(balance)
        elif is_class(balance, unrealsdk.FindClass("ClassModBalanceDefinition")):
            inventory_definition, manufacturer = self.get_com_data(balance)
        else:
            inventory_definition, manufacturer = self.get_item_data(balance)

        item = get_pc().Spawn(inventory_definition.InventoryClass)
        item.Gamestage = level
        item.InitializeInventory(balance, manufacturer, level, None)
        return item

    def get_balance_from_pool(self, pool: unrealsdk.UObject):
        obj = pool
        pool_cls = unrealsdk.FindClass("ItemPoolDefinition")
        while is_class(obj, pool_cls):
            obj = choices(
                [
                    item.ItmPoolDefinition
                    if item.InvBalanceDefinition is None
                    else item.InvBalanceDefinition
                    for item in obj.BalancedItems
                ],
                [self.eval_aid(item.Probability) for item in obj.BalancedItems],
            )[0]
        return obj

    def get_reward_data(self, mission: unrealsdk.UObject, alt: bool) -> tuple:
        mission_reward = mission.AlternativeReward if alt else mission.Reward
        items = []
        items.extend(mission_reward.RewardItems)
        items.extend(mission_reward.RewardItemPools)
        if len(items) > 2:
            items = items[0:2]
        for idx, item in enumerate(items):
            items[idx] = self.create_from_balance(
                self.get_balance_from_pool(item), mission.GetGameStage()
            )
        weapon_rewards = []
        item_rewards = []
        for item in items:
            if "Weapon" in item.Class.Name:
                weapon_rewards.append(WeaponDefinitionData(item.DefinitionData))
                continue
            item_rewards.append(ItemDefinitionData(item.DefinitionData))
        for _ in range(2 - len(weapon_rewards)):
            weapon_rewards.append(WeaponDefinitionData())
        for _ in range(2 - len(item_rewards)):
            item_rewards.append(ItemDefinitionData())
        return (mission, weapon_rewards, item_rewards, alt)

    def earn_mission_xp(self, mission: unrealsdk.UObject, alt: bool):
        PC = get_pc()
        xp = mission.GetExperienceReward(PC, alt)
        if xp > 0:
            source = (
                EExperienceSource.EES_PlotMissionAward
                if mission.bPlotCritical
                else EExperienceSource.EES_SideMissionAward
            )
            PC.ExpEarn(xp, source)

    def earn_mission_currency(self, mission: unrealsdk.UObject, alt: bool):
        PC = get_pc()
        rep_info = PC.PlayerReplicationInfo
        currency_type = mission.GetCurrencyRewardType(alt)
        currency_reward = mission.GetCurrencyReward(PC, alt)
        if currency_reward > 0:
            rep_info.AddCurrencyOnHand(currency_type, currency_reward)
        if currency_type != ECurrencyType.CURRENCY_Credits:
            currency_reward = mission.GetOptionalCreditReward(PC)
            if currency_reward > 0:
                rep_info.AddCurrencyOnHand(ECurrencyType.CURRENCY_Credits, currency_reward)

    def roll_mission_reward(self, mission: unrealsdk.UObject, alt: bool):
        PC = get_pc()
        if PC.GFxUIManager.IsMoviePlaying(self.quest_movie_def):
            PC.GFxUIManager.GetPlayingMovie().DisplayRewardsPage(self.get_reward_data(mission, alt))
            return
        unclaimed_rewards = [
            PendingMissionRewardData(unclaimed_reward) for unclaimed_reward in PC.UnclaimedRewards
        ]
        unclaimed_rewards.append(self.get_reward_data(mission, alt))
        PC.UnclaimedRewards = unclaimed_rewards
        PC.GFxUIManager.GetPlayingMovie().Close()
        PC.ContextualPromptScreen = EBackButtonScreen.CS_Inventory
        PC.myHUD.PlayStatusMovie()

    def grant_rewards(self, mission: unrealsdk.UObject):
        PC = get_pc()
        mission_status = PC.GetPlayersMissionStatus(mission)
        if mission_status not in [
            EMissionStatus.MS_ReadyToTurnIn,
            EMissionStatus.MS_RequiredObjectivesComplete,
        ]:
            if not PC.GFxUIManager.IsMoviePlaying(self.quest_movie_def):
                PC.WorldInfo.GRI.MissionTracker.CompleteMission(mission, PC)
            return
        pt = PC.GetCurrentPlaythrough()
        idx = PC.NativeGetMissionIndex(mission)
        progress = PC.MissionPlaythroughs[pt].MissionList[idx].ObjectivesProgress
        progress = PC.MissionPlaythroughs[pt].MissionList[idx].ObjectivesProgress
        alt, _ = mission.ShouldGrantAlternateReward(progress)
        self.earn_mission_xp(mission, alt)
        self.earn_mission_currency(mission, alt)
        self.roll_mission_reward(mission, alt)

    @ClientMethod
    def client_grant_rewards(self, mission_name: str):
        mission = get_mission(mission_name)
        self.grant_rewards(mission)

    @ServerMethod
    def server_grant_rewards(self, mission_name: str):
        self.client_grant_rewards(mission_name)
        mission = get_mission(mission_name)
        self.grant_rewards(mission)

    @Hook("WillowGame.LatentRewardGFxMovie.HandleRewardInputKey")
    @Hook("WillowGame.QuestAcceptGFxMovie.HandleRewardInputKey")
    def handle_reroll_input(
        self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct
    ) -> bool:
        if params.uevent != EInputEvent.IE_Pressed:
            return True
        PC = this.WPCOwner
        mission = this.RewardObject.RewardData.Mission
        alt = this.RewardObject.RewardData.bGrantAltReward
        if check_accept_input(params.ukey):
            mission_status = PC.GetPlayersMissionStatus(mission)
            if mission_status in [
                EMissionStatus.MS_ReadyToTurnIn,
                EMissionStatus.MS_RequiredObjectivesComplete,
            ]:
                PC.WorldInfo.GRI.MissionTracker.CompleteMission(mission, PC)
            return True
        if not check_reroll_input(PC, params.ukey):
            return True
        rep_info = PC.PlayerReplicationInfo
        currentEridium = rep_info.GetCurrencyOnHand(ECurrencyType.CURRENCY_Eridium)
        if currentEridium < self.eridiumCost:
            return True
        rep_info.AddCurrencyOnHand(ECurrencyType.CURRENCY_Eridium, (self.eridiumCost * -1))
        if is_class(this, unrealsdk.FindClass("LatentRewardGFxMovie")):
            PC.GFxUIManager.GetPlayingMovie().DisplayRewardsPanel(
                self.get_reward_data(mission, alt)
            )
        else:
            PC.GFxUIManager.GetPlayingMovie().DisplayRewardsPage(self.get_reward_data(mission, alt))
        return True

    @Hook("WillowGame.WillowPlayerController.ServerCompleteMission")
    def handle_server_complete_mission(
        self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct
    ) -> bool:
        unrealsdk.Log("ServerCompleteMission")
        return True

    @Hook("WillowGame.MissionTracker.CompleteMission")
    def handle_tracker_complete_mission(
        self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct
    ) -> bool:
        return False

    @Hook("WillowGame.WillowPlayerController.ServerGrantMissionRewards")
    def handle_grant_rewards(
        self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct
    ) -> bool:

        return False

    @Hook("WillowGame.QuestAcceptGFxMovie.extCompleteConfirmed")
    def handle_complete_mission(
        self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct
    ) -> bool:
        PC = this.WPCOwner
        mission = this.MissionList[this.GetSelectedIndex()].MissionDef

        if is_client():
            self.server_grant_rewards(this.PathName(mission))
        else:
            self.client_grant_rewards(this.PathName(mission))
            self.grant_rewards(mission)

        mission_status = PC.GetPlayersMissionStatus(mission)
        if mission_status not in [
            EMissionStatus.MS_ReadyToTurnIn,
            EMissionStatus.MS_RequiredObjectivesComplete,
        ]:
            PC.WorldInfo.GRI.MissionTracker.CompleteMission(mission, PC)
            return True
        return False

    @Hook("WillowGame.MissionRewardGFxObject.SetTooltips")
    def set_tooltips(
        self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct
    ) -> bool:
        PC = this.OwningMovie.GetPC()
        if PC.PlayerInput.bUsingGamepad == False:
            secondaryUse = f"[{PC.PlayerInput.GetKeyForAction('UseSecondary', True)}]"
        else:
            secondaryUse = "(Y)"

        if PC.PlayerInput.bUsingGamepad == False:
            inspectKey = "[F]"
        else:
            inspectKey = "(R)"

        if PC.PlayerInput.bUsingGamepad == False:
            acceptKey = "[Enter]"
        else:
            acceptKey = "(A)"

        this.GetObject("tooltips").SetString(
            "htmlText",
            f"{acceptKey} Accept  {inspectKey} Inspect\n{secondaryUse} Reroll ({self.eridiumCost}E/{PC.PlayerReplicationInfo.GetCurrencyOnHand(1)}E)",
        )
        return False


instance = RewardReroller()
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
