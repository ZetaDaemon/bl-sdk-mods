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
    TextColour: tuple = (
        0,
        0,
        0,
        255
    )
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
        self.RedSlider = Options.Slider (
            Caption="Red",
            Description="Red value for the text colour.",
            StartingValue=255,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.GreenSlider = Options.Slider (
            Caption="Green",
            Description="Green value for the text colour.",
            StartingValue=50,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BlueSlider = Options.Slider (
            Caption="Blue",
            Description="Blue value for the text colour.",
            StartingValue=165,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.TextColour = Options.Nested (
            Caption = "Text Colour",
            Description = "Text colour for the farm counter.",
            Children = [RedSlider, GreenSlider, BlueSlider],
            IsHidden = False
        )
        self.SizeSlider = Options.Slider (
            Caption="Font Size",
            Description="Font scaling as a percentage.",
            StartingValue=100,
            MinValue=0,
            MaxValue=200,
            Increment=1,
            IsHidden=False
        )
        self.xPosSlider = Options.Slider (
            Caption="X Position",
            Description="X position for the text.",
            StartingValue=50,
            MinValue=0,
            MaxValue=UCanvas.SizeX,
            Increment=1,
            IsHidden=False
        )
        self.yPosSlider = Options.Slider (
            Caption="Y Position",
            Description="Y position for the text.",
            StartingValue=50,
            MinValue=0,
            MaxValue=UCanvas.SizeY,
            Increment=1,
            IsHidden=False
        )
        self.TextPos = Options.Nested (
            Caption = "Text Position",
            Description = "Text position for the farm counter.",
            Children = [xPosSlider, yPosSlider],
            IsHidden = False
        )
        self.Options = [
            TextColour,
            SizeSlider,
            TextPos
        ]

    def ModOptionChanged(self, option: ModMenu.Options.Base, new_value) -> None:
        if option == self.xPosSlider:
            self.x = new_value
        if option == self.yPosSlider:
            self.y = new_value

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
            self.DrawText(canvas, self.MessageText.format(self.FarmName, self.FarmName), self.x, self.y, self.TextColour, 1, 1)
        elif not self.Farming: 
            self.Farming = False
        return True

    def GameInputPressed(self, input):
        if input.Name == "Toggle Farming":
            self.Farming = not self.Farming
            #self.displayFeedback()
        if input.Name == "Get Farm Name":
            pass

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