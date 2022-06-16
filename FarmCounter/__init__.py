from unrealsdk import *
from Mods.ModMenu import RegisterMod, SDKMod, Options
from Mods.UserFeedback import TextInputBox


class FarmCounter(SDKMod):
    Name: str = "Farm Counter"
    Author: str = "ZetaDæmon"
    Description: str = (
        "Adds a simple farm counter to track how many times you have run the current farm."
    )
    Version: str = "1.0"

    Farming: bool = False
    RunCount: int = 0
    FarmName: str = ""
    x: int = 50
    y: int = 50
    alpha: int = 255
    FarmNameInput = TextInputBox("Farm Name", "Enter farm name: ")
    MessageText: str = (
        "Farming: {}\n"
        "Run: {}"
    )

    Keybinds: List[ModMenu.Keybind] = [
        ModMenu.Keybind("Toggle Farming", "F3"),
        ModMenu.Keybind("Get Farm Name", "F4"),
    ]

    def __init__(self) -> None:
        self.Options = []
        RedSlider: Options.Slider
        BlueSlider: Options.Slider
        GreenSlider: Options.Slider
        SizeSlider: Options.Slider
        TextColour: Options.Nested
        RedSlider = Options.Slider (
            Caption="Red",
            Description="Red value for the text colour.",
            StartingValue=50,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        GreenSlider = Options.Slider (
            Caption="Green",
            Description="Green value for the text colour.",
            StartingValue=50,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        BlueSlider = Options.Slider (
            Caption="Blue",
            Description="Blue value for the text colour.",
            StartingValue=50,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        SizeSlider = Options.Slider (
            Caption="Font Size",
            Description="Font scaling as a percentage.",
            StartingValue=100,
            MinValue=0,
            MaxValue=200,
            Increment=1,
            IsHidden=False
        )
        TextColour = Options.Nested (
            Caption = "Text Colour",
            Description = "Text colour for the farm counter.",
            Children = [RedSlider, GreenSlider, BlueSlider],
            IsHidden = False
        )
        self.Options.append(TextColour)
        self.Options.append(SizeSlider)

    def DrawText(self, canvas, text, x, y, color, scalex, scaley) -> None:
        canvas.Font = unrealsdk.FindObject("Font", "ui_fonts.font_willowbody_18pt")

        canvas.SetPos(x, y, 0)
        canvas.SetDrawColorStruct(color) #b, g, r, a
        canvas.DrawText(text, False, scalex, scaley, ())
        self.NumDisplayedCounters += 1

    def displayFeedback(self):
        if self.Farming:           
            if not params.Canvas:
                return True

            canvas = params.Canvas
            self.DrawText(canvas, self.MessageText.format(self.FarmName, self.FarmName), self.x, self.y, (0, 165, 255, self.alpha), 1, 1)
        elif not self.Farming: 
            self.Farming = False
        return True

    def GameInputPressed(self, input):
        if input.Name == "Toggle Farming":
            self.Farming = not self.Farming
            self.displayFeedback()
        if input.Name == "Get Farm Name":

    def Enable(self):

        def onSaveQuit(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> None:
                self.RunCount += 1
                return True

        def onPostRender(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            self.displayFeedback()
            return True

        RegisterHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender", onPostRender)
        RegisterHook("WillowGame.PauseGFxMovie.CompleteQuitToMenu", "SaveQuit", onSaveQuit)
        RegisterHook("Engine.PlayerController.NotifyDisconnect", "QuitWithoutSaving", onSaveQuit)

    def Disable(self):
        RemoveHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender")
        RemoveHook("WillowGame.PauseGFxMovie.CompleteQuitToMenu", "SaveQuit")
        RemoveHook("Engine.PlayerController.NotifyDisconnect", "QuitWithoutSaving")

RegisterMod(FarmCounter())