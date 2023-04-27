import unrealsdk
from Mods.ModMenu import ModTypes, RegisterMod, SDKMod, EnabledSaveType, Keybind, Options, Mods, Hook

class DialogSkipper(SDKMod):
	Name: str = "Dialog Skipper"
	Author: str = "ZetaDaemon"
	Description: str = (
		"Allows for skipping dialog."
	)
	Version: str = "1.0"
	Types: ModTypes = ModTypes.Utility
	SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

	Keybinds: list = [
		Keybind("Skip Dialog", "Z")
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
	
	def GameInputPressed(self, input):
		if input.Name == "Skip Dialog":
			for dialog in unrealsdk.FindAll("GearboxDialogComponent"):
				if not dialog.IsTalking():
					continue
				dialog.StopTalking()
	
	@Hook("GearboxFramework.GearboxDialogComponent.TriggerEvent")
	def skip_dialog(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
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
