import unrealsdk
from Mods.ModMenu import SDKMod, EnabledSaveType, ModTypes, Game

class MovementTech(SDKMod):
    Name: str = "Movement Tech"
    Description: str = "Allows for slamming and double jumps for BL2."
    Author: str = "ZetaDæmon"
    Version: str = "1.0"
    SupportedGames = Game.BL2
    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    Want_To_Slam: bool = False
    Slam_Speed = -6000
    Slam_Start_Height = 0
    Min_Slam_Height = 210
    Slam_Radius = 500
    Base_Impact_Particle = "FX_CHAR_Shared_Shield.Particles.Novas.Part_Explosive_Nova_Shield_Explosion"
    Custom_Impact_Particle_Name = "Slam_Custom_Explosion"
    Impact_Sound = "Ake_Exp_Elemental.Exp_Explosive.Ak_Play_Exp_Elemental_Explosive_MED"

    Wants_To_Double_Jump = False
    Double_Jumped = False
    Jump_Velocity = 420
    Jump_Sound = "Ake_Fs_Player.Ak_Play_Fs_Jump"


    def slam_damage(self, power) -> float:
        multiplier = 8
        level = unrealsdk.FindObject("ConstantAttributeValueResolver", "GD_Balance_HealthAndDamage.HealthAndDamage.Att_UniversalBalanceScaler:ConstantAttributeValueResolver_0").ConstantValue
        return multiplier*(pow(level, power))

    def construct_particle(self):
        src = unrealsdk.FindObject("ParticleSystem", self.Base_Impact_Particle).ObjectArchetype
        Base_Particle = unrealsdk.FindObject("ParticleSystem", self.Base_Impact_Particle)
        self.Custom_Impact_Particle = unrealsdk.ConstructObject(
            Class=src.Class,
            Outer=Base_Particle.Outer,
            Name=self.Custom_Impact_Particle_Name,
            Template=src
        )
        unrealsdk.KeepAlive(self.Custom_Impact_Particle)
        self.Custom_Impact_Particle.ObjectArchetype = src.ObjectArchetype
        self.Custom_Impact_Particle.ObjectFlags.B |= 4
        Base_Particle = unrealsdk.FindObject("ParticleSystem", self.Base_Impact_Particle)
        Base_Emitters = getattr(Base_Particle, "Emitters")
        New_Emitters = [Base_Emitters[1]]
        setattr(self.Custom_Impact_Particle, "Emitters", New_Emitters)

    def start_slam(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if self.Want_To_Slam:
            return
        pc = caller.Outer
        if not pc.Pawn:
            return True

        # Only allow slam while in air
        if not pc.Pawn.IsOnGroundOrShortFall():
            self.slam()
            return False
        return True

    def slam(self) -> None:
        pc = unrealsdk.GetEngine().GamePlayers[0].Actor
        pawn = pc.Pawn
        if pawn is None:
            return

        self.Slam_Start_Height = pawn.Location.Z
        self.Want_To_Slam = True
        self.Fall_Direction = (0, 0, self.Slam_Speed)

    def jump(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if self.Double_Jumped:
            return True
        if self.Want_To_Slam:
            return True
        pc = caller.Outer
        if not pc.Pawn:
            return True
        if not pc.Pawn.IsOnGroundOrShortFall():
            self.Wants_To_Double_Jump = True
        return True

    def tick_player(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        pawn = caller.Pawn
        if pawn is None:
            return True

        grounded = pawn.IsOnGroundOrShortFall()
        if self.Want_To_Slam:
            
            pawn.Velocity = self.Fall_Direction
            if grounded:
                self.Want_To_Slam = False
                falldistance = self.Slam_Start_Height - pawn.Location.Z
                if falldistance > self.Min_Slam_Height:
                    emitter_pool = unrealsdk.GetEngine().GetCurrentWorldInfo().MyEmitterPool
                    player_location = (pawn.Location.X, pawn.Location.Y, pawn.Location.Z)
                    emitter_pool.SpawnEmitter(self.Custom_Impact_Particle, player_location,)
                    pawn.PlayAkEvent(unrealsdk.FindObject("AkEvent", self.Impact_Sound))
                    damage_multiplier = 3 + 0.5*falldistance/self.Min_Slam_Height
                    pawn.Behavior_CauseRadiusDamage(
                        self.Slam_Radius, 
                        damage_multiplier * self.slam_damage(pawn.GetExpLevel()),
                        True,
                        0,
                        unrealsdk.FindClass("DmgType_Crushed"),
                        unrealsdk.FindObject("WillowDamageTypeDefinition", "GD_Explosive.DamageType.DmgType_Explosive_Impact"),
                        unrealsdk.FindObject("WillowExplosionImpactDefinition", "GD_Impacts.ExplosiveImpacts.ExplosiveImpactNormal128"),
                        False
                        )

        if self.Wants_To_Double_Jump:
            self.Wants_To_Double_Jump = False
            self.Double_Jumped = True
            _x, _y = pawn.Velocity.X, pawn.Velocity.Y
            pawn.Velocity = (_x, _y, self.Jump_Velocity)
            pawn.PlayAkEvent(unrealsdk.FindObject("AkEvent", self.Jump_Sound))

        if self.Double_Jumped:
            if grounded:
                self.Double_Jumped = False

        return True

    def Enable(self) -> None:
        self.construct_particle()
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "TickPlayer", 
            lambda c, f, p : self.tick_player(c, f, p))
        unrealsdk.RegisterHook("WillowGame.WillowPlayerInput.DuckPressed", "SlamInputStart",
            lambda c, f, p : self.start_slam(c, f, p))
        unrealsdk.RegisterHook("WillowGame.WillowPlayerInput.Jump", "Jumped",
            lambda c, f, p : self.jump(c, f, p))

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "TickPlayer")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerInput.DuckPressed", "SlamInputStart")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerInput.Jump", "Jumped")


unrealsdk.RegisterMod(MovementTech())
