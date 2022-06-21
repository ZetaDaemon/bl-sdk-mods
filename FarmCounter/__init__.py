import unrealsdk
from Mods.ModMenu import RegisterMod, SDKMod, Options, Keybind, EnabledSaveType, Mods, ModTypes
try:
  from Mods.UserFeedback import TextInputBox
except ImportError as ex:
  unrealsdk.Log("Unable to load FarmCounter, missing UserFeedback")
  raise ex
from types import ModuleType
from typing import Tuple, Optional
import re

Quickload: Optional[ModuleType]
try:
    from Mods import Quickload
except ImportError:
    Quickload = None

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
    RunCount: int = 1
    FarmName: str = ""
    MessageText = """ Farming: {} 
 Run #{} """
    M1 = " Farming: {} "
    M2 = " Run #{} "
    HasOverriddenML: bool = False

    Keybinds: list = [
        Keybind("Toggle Farming", "F3"),
        Keybind("Get Farm Name", "F4"),
        Keybind("Get Farm Count", "Insert"),
        Keybind("Increase Farm Count", "PageUp"),
        Keybind("Decrease Farm Count", "PageDown"),
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
            StartingValue=45,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BackgroundSize = Options.Slider (
            Caption="Background Size",
            Description="Size for the text Background.",
            StartingValue=100,
            MinValue=50,
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

        self.GlowRedSlider = Options.Slider (
            Caption="Red",
            Description="Red value for the Glow colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.GlowGreenSlider = Options.Slider (
            Caption="Green",
            Description="Green value for the Glow colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.GlowBlueSlider = Options.Slider (
            Caption="Blue",
            Description="Blue value for the Glow colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.GlowAlphaSlider = Options.Slider (
            Caption="Alpha",
            Description="Alpha value for the Glow colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.GlowSize = Options.Slider (
            Caption="Glow Size",
            Description="Size for the text Glow.",
            StartingValue=0,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.GlowSettings = Options.Nested (
            Caption = "Glow Settings",
            Description = "Glow settings for the farm counter.",
            Children = [self.GlowRedSlider, self.GlowGreenSlider, self.GlowBlueSlider, self.GlowAlphaSlider, self.GlowSize],
            IsHidden = True
        )

        self.SizeSlider = Options.Slider (
            Caption="Counter Size",
            Description="Counter scaling as a percentage.",
            StartingValue=130,
            MinValue=50,
            MaxValue=300,
            Increment=1,
            IsHidden=False
        )

        self.xPosSlider = Options.Slider (
            Caption="X Position",
            Description="X position for the counter as a percentage of the total screen.",
            StartingValue=1,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.yPosSlider = Options.Slider (
            Caption="Y Position",
            Description="Y position for the counter as a percentage of the total screen.",
            StartingValue=1,
            MinValue=0,
            MaxValue=100,
            Increment=1,
            IsHidden=False
        )
        self.CounterPos = Options.Nested (
            Caption = "Counter Position",
            Description = "Text position for the farm counter.",
            Children = [self.xPosSlider, self.yPosSlider],
            IsHidden = False
        )

        self.AutoCount = Options.Boolean (
            Caption = "Automatic Counting",
            Description = "Enable or disable automatic incrementing of the farm counter on save quit.",
            StartingValue = True,
            Choices = ("Off", "On"),
            IsHidden = False
        )
        self.Options = [
            self.TextColour,
            self.BackgroundSettings,
            self.GlowSettings,
            self.CounterPos,
            self.SizeSlider,
            self.AutoCount
        ]

    def DisplayText(self, canvas, text, x, y, color, scalex, scaley, BackgroundColour, BackgroundScale, FontRenderInfo) -> None:
        canvas.Font = unrealsdk.FindObject("Font", "UI_Fonts.Font_Willowbody_18pt")
        texture = unrealsdk.FindObject("Texture2D", "EngineResources.WhiteSquareTexture")

        trueX = canvas.SizeX * x
        trueY = canvas.SizeX * y

        x1, y1 = canvas.TextSize(self.M1.format(self.FarmName), 0, 0)
        x2, y2 = canvas.TextSize(self.M2.format(self.RunCount), 0, 0)
        backgroundX = x1 if x1 > x2 else x2
        backgroundY = (y1 + y2)

        canvas.SetPos(trueX-(0.5*backgroundX*scalex*(BackgroundScale-1)), trueY-(0.5*backgroundY*scaley*(BackgroundScale-1)), 0)

        try:
            canvas.SetDrawColorStruct(BackgroundColour) #b, g, r, a
        except:
            pass
        canvas.DrawRect(backgroundX*BackgroundScale*scalex, backgroundY*BackgroundScale*scaley, texture)
                
        canvas.SetPos(trueX, trueY, 0)
        try:
            canvas.SetDrawColorStruct(color) #b, g, r, a
        except:
            pass
        
        canvas.DrawText(text, False, scalex, scaley, FontRenderInfo)

    def displayFeedback(self, params):
        if unrealsdk.GetEngine().GetCurrentWorldInfo().GetStreamingPersistentMapName().lower() == "menumap":
            return True
        if self.Farming:           
            if not params.Canvas:
                return True

            canvas = params.Canvas
            glowColour = (
                self.GlowRedSlider.CurrentValue, 
                self.GlowGreenSlider.CurrentValue, 
                self.GlowBlueSlider.CurrentValue, 
                self.GlowAlphaSlider.CurrentValue
            )
            glowRadius = (
                self.GlowSize.CurrentValue,
                self.GlowSize.CurrentValue
            )
            gInfo = (
                True,
                glowColour,
                glowRadius,
                glowRadius
            )
            FontRenderInfo = (
                False,
                True,
                gInfo
            )
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
                self.BackgroundSize.CurrentValue/100,
                FontRenderInfo
            )
        return True

    def GetFarmName(self):
        FarmNameInput = TextInputBox("Enter Farm Name", "")
        def setFarmName(Message: str) -> None:
            self.FarmName = Message
        FarmNameInput.OnSubmit = setFarmName
        FarmNameInput.Show()

    def GetFarmCount(self):
        FarmCountInput = TextInputBox("Enter Farm Count", "")
        FarmCountInput.IsAllowedToWrite = lambda c, m, p: c in "0123456789"
        def setFarmCount(Message: str) -> None:
            self.RunCount = int(Message)
        FarmCountInput.OnSubmit = setFarmCount
        FarmCountInput.Show()


    def GameInputPressed(self, input):
        if input.Name == "Toggle Farming":
            self.Farming = not self.Farming
            if not self.Farming:
                self.RunCount = 1
                self.FarmName = ""

        elif input.Name == "Get Farm Name":
            self.GetFarmName()
        elif input.Name == "Get Farm Count":
            self.GetFarmCount()
        elif input.Name == "Increase Farm Count":
            self.AddToCounter(1)
        elif input.Name == "Decrease Farm Count":
            if self.RunCount > 1:
                self.AddToCounter(-1)

    def AddToCounter(self, n):
        if self.Farming:
            self.RunCount += n

    def FC_ReloadCurrentMap(self, skipSave):
        self.AddToCounter(1)
        self.ML_ReloadCurrentMap(skipSave)

    def Enable(self):

        def onSaveQuit(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if self.AutoCount.CurrentValue:
                    self.AddToCounter(1)
                return True

        def onPostRender(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            self.displayFeedback(params)
            return True

        if not self.HasOverriddenML:
            if Quickload is not None:
                self.ML_ReloadCurrentMap = Quickload._ReloadCurrentMap
                Quickload._ReloadCurrentMap = self.FC_ReloadCurrentMap
                self.HasOverriddenML = True
        unrealsdk.RegisterHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender", onPostRender)
        unrealsdk.RegisterHook("WillowGame.PauseGFxMovie.CompleteQuitToMenu", "SaveQuit", onSaveQuit)
        unrealsdk.RegisterHook("Engine.PlayerController.NotifyDisconnect", "QuitWithoutSaving", onSaveQuit)

    def Disable(self):
        if Quickload is not None:
            self.ML_ReloadCurrentMap = Quickload._ReloadCurrentMap
            Quickload._ReloadCurrentMap = self.FC_ReloadCurrentMap
            self.HasOverriddenML = False
        unrealsdk.RemoveHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender")
        unrealsdk.RemoveHook("WillowGame.PauseGFxMovie.CompleteQuitToMenu", "SaveQuit")
        unrealsdk.RemoveHook("Engine.PlayerController.NotifyDisconnect", "QuitWithoutSaving")

RegisterMod(FarmCounter())