import unrealsdk
from Mods.ModMenu import RegisterMod, SDKMod, Options, EnabledSaveType, ModTypes


class ConsoleFontSize(SDKMod):
    Name: str = "Console Font Size"
    Author: str = "ZetaDæmon"
    Description: str = "Adds a slider to change the font size of console"
    Version: str = "1.0"
    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    def __init__(self) -> None:
        self.Options = []
        self.FontSizeSlider = Options.Slider(
            Caption="Font Size",
            Description="Console Font Size, default size is 16",
            StartingValue=16,
            MinValue=1,
            MaxValue=64,
            Increment=1,
            IsHidden=False,
        )
        self.Options.append(self.FontSizeSlider)

    def ModOptionChanged(self, option, newValue) -> None:
        if option != self.FontSizeSlider:
            return
        font = unrealsdk.FindObject("Font", "EngineFonts.SmallFont")
        font.MaxCharHeight = [newValue]
        font.ScalingFactor = newValue / 16.0

    def Enable(self) -> None:
        super().Enable()


RegisterMod(ConsoleFontSize())
