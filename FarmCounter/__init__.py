import unrealsdk
from Mods.ModMenu import RegisterMod, SDKMod, Options, Keybind, EnabledSaveType, Mods, ModTypes
from Mods.UserFeedback import TextInputBox
from typing import Tuple



class FarmCounter(SDKMod):
    Name: str = "Farm Counter"
    Author: str = "ZetaDæmon"
    Description: str = (
        "Adds a simple farm counter to track how many times you have run the current farm."
    )
    Version: str = "1.0"
    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    Farming: bool = False
    isFarming: bool = False
    RunCount: int = 0
    FarmName: str = ""
    MessageText = """Farming: {}
Run: {}"""

    Keybinds: list = [
        Keybind("Toggle Farming", "F3"),
        Keybind("Get Farm Name", "F4"),
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
            StartingValue=170,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BlueSlider = Options.Slider (
            Caption="Blue",
            Description="Blue value for the text colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.AlphaSlider = Options.Slider (
            Caption="Alpha",
            Description="Alpha value for the text colour.",
            StartingValue=255,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.TextColour = Options.Nested (
            Caption = "Text Colour",
            Description = "Text colour for the farm counter.",
            Children = [self.RedSlider, self.GreenSlider, self.BlueSlider, self.AlphaSlider],
            IsHidden = False
        )

        self.BackgroundRedSlider = Options.Slider (
            Caption="Red",
            Description="Red value for the Background colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BackgroundGreenSlider = Options.Slider (
            Caption="Green",
            Description="Green value for the Background colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BackgroundBlueSlider = Options.Slider (
            Caption="Blue",
            Description="Blue value for the Background colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BackgroundAlphaSlider = Options.Slider (
            Caption="Alpha",
            Description="Alpha value for the Background colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BackgroundSize = Options.Slider (
            Caption="Background Size",
            Description="Size for the text Background.",
            StartingValue=0,
            MinValue=25,
            MaxValue=300,
            Increment=1,
            IsHidden=False
        )
        self.BackgroundSettings = Options.Nested (
            Caption = "Background Settings",
            Description = "Background settings for the farm counter.",
            Children = [self.BackgroundRedSlider, self.BackgroundGreenSlider, self.BackgroundBlueSlider, self.BackgroundAlphaSlider, self.BackgroundSize],
            IsHidden = False
        )

        self.SizeSlider = Options.Slider (
            Caption="Font Size",
            Description="Font scaling as a percentage.",
            StartingValue=100,
            MinValue=50,
            MaxValue=300,
            Increment=1,
            IsHidden=False
        )

        self.xPosSlider = Options.Slider (
            Caption="X Position",
            Description="X position for the counter as a percentage of the total screen.",
            StartingValue=2,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.yPosSlider = Options.Slider (
            Caption="Y Position",
            Description="Y position for the counter as a percentage of the total screen.",
            StartingValue=2,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.CounterPos = Options.Nested (
            Caption = "Text Position",
            Description = "Text position for the farm counter.",
            Children = [self.xPosSlider, self.yPosSlider],
            IsHidden = False
        )
        self.Options = [
            self.TextColour,
            self.BackgroundSettings,
            self.CounterPos,
            self.SizeSlider
        ]

    def DisplayText(self, canvas, text, x, y, color, scalex, scaley, BackgroundColour, BackgroundScale) -> None:
        canvas.Font = unrealsdk.FindObject("Font", "UI_Fonts.Font_Willowbody_18pt")

        trueX = canvas.SizeX * x
        trueY = canvas.SizeX * y
        canvas.SetPos(trueX, trueY, 0)
        ret, backgroundX, backgroundY = canvas.TextSize(text, 0, 0)

        try:
            canvas.SetDrawColorStruct(BackgroundColour) #b, g, r, a
        except:
            pass
        canvas.DrawBox(backgroundX*BackgroundScale, backgroundY*BackgroundScale)

        try:
            canvas.SetDrawColorStruct(color) #b, g, r, a
        except:
            pass
        canvas.DrawText(text, False, scalex, scaley, ())

    def displayFeedback(self, params):
        if self.Farming:           
            if not params.Canvas:
                return True

            canvas = params.Canvas
            self.DisplayText(
                canvas, 
                self.MessageText.format(self.FarmName, self.RunCount), 
                self.xPosSlider.CurrentValue / 100, 
                self.yPosSlider.CurrentValue / 100, 
                (
                    self.BlueSlider.CurrentValue,
                    self.GreenSlider.CurrentValue,
                    self.RedSlider.CurrentValue,
                    self.AlphaSlider.CurrentValue
                ), 
                self.SizeSlider.CurrentValue / 100, 
                self.SizeSlider.CurrentValue / 100,
                (
                    self.BackgroundBlueSlider.CurrentValue, 
                    self.BackgroundGreenSlider.CurrentValue, 
                    self.BackgroundRedSlider.CurrentValue, 
                    self.BackgroundAlphaSlider.CurrentValue
                ),
                self.BackgroundSize.CurrentValue/100 * self.SizeSlider.CurrentValue/100
            )
        elif not self.Farming: 
            self.Farming = False
        return True

    def GetFarmName(self):
        FarmNameInput = TextInputBox("Enter Farm Name", "")
        def setFarmName(Message: str) -> None:
            self.FarmName = Message
        FarmNameInput.OnSubmit = setFarmName
        FarmNameInput.Show()


    def GameInputPressed(self, input):
        if input.Name == "Toggle Farming":
            self.Farming = not self.Farming
            if not self.Farming:
                self.RunCount = 0
                self.FarmName = ""

        if input.Name == "Get Farm Name":
            self.GetFarmName()

    def Enable(self):

        def onSaveQuit(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                self.RunCount += 1
                if self.Farming:
                    self.isFarming = self.Farming
                    self.Farming = False
                return True

        def onPostRender(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            self.displayFeedback(params)
            return True

        def OnLoad(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if self.isFarming:
                    self.Farming = self.isFarming

        unrealsdk.RegisterHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender", onPostRender)
        unrealsdk.RegisterHook("WillowGame.PauseGFxMovie.CompleteQuitToMenu", "SaveQuit", onSaveQuit)
        unrealsdk.RegisterHook("Engine.PlayerController.NotifyDisconnect", "QuitWithoutSaving", onSaveQuit)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "OnLoad", OnLoad)

    def Disable(self):
        unrealsdk.RemoveHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender")
        unrealsdk.RemoveHook("WillowGame.PauseGFxMovie.CompleteQuitToMenu", "SaveQuit")
        unrealsdk.RemoveHook("Engine.PlayerController.NotifyDisconnect", "QuitWithoutSaving")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "OnLoad")

RegisterMod(FarmCounter())