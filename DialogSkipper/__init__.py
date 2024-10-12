import unrealsdk
from Mods.ModMenu import ModTypes, RegisterMod, SDKMod, EnabledSaveType, Keybind, Options, Mods, Hook, SaveModSettings

class DialogSkipper(SDKMod):
	Name: str = "Dialog Skipper"
	Author: str = "ZetaDaemon"
	Description: str = (
		"Allows for skipping dialog."
	)
	Version: str = "1.2"
	Types: ModTypes = ModTypes.Utility
	SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

	Keybinds: list = [
		Keybind("Skip Dialog", "Z"),
		Keybind("Toggle Always Skip", "X")
	]

	def __init__(self):
		self.always_skip = Options.Boolean (
			Caption = "Always Skip",
			Description = "Always skip dialog, stopping any from playing",
			StartingValue = False,
			Choices = ("Off", "On"),
			IsHidden = False
		)

		self.Options = [
			self.always_skip
		]
	
	def training_text(self, message: str, duration: float = 2.0) -> None:
		pc = unrealsdk.GetEngine().GamePlayers[0].Actor

		hud_movie = pc.GetHUDMovie()
		if hud_movie is None:
			return

		hud_movie.ClearTrainingText()
		hud_movie.AddTrainingText(
			message,
			self.Name,
			duration,
			(),
			"",
			False,
			0,
			pc.PlayerReplicationInfo,
			True
		)

	def skip_dialog(self) -> None:
		for dialog in unrealsdk.FindAll("GearboxDialogComponent"):
			if not dialog.IsTalking():
				continue
			dialog.StopTalking()

	def GameInputPressed(self, input):
		if input.Name == "Skip Dialog":
			self.skip_dialog()
		elif input.Name == "Toggle Always Skip":
			if self.always_skip.CurrentValue:
				self.always_skip.CurrentValue = False
				self.training_text("Always Skip: Off")
			else:
				self.always_skip.CurrentValue = True
				self.training_text("Always Skip: On")
				self.skip_dialog()
			SaveModSettings(instance)
	
	@Hook("GearboxFramework.GearboxDialogComponent.TriggerEvent")
	def trigger_event(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
		if self.always_skip.CurrentValue:
			return False
		return True
	
	@Hook("GearboxFramework.Behavior_TriggerDialogEvent.TriggerDialogEvent")
	def trigger_dialog(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
		if self.always_skip.CurrentValue:
			return False
		return True
	
	@Hook("WillowGame.WillowDialogAct_Talk.Activate")
	def talk_activate(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
		if self.always_skip.CurrentValue:
			return False
		return True


instance = DialogSkipper()
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
