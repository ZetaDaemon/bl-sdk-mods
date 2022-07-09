import unrealsdk
from Mods.ModMenu import SDKMod, EnabledSaveType, ModTypes, Game


class MovementTech(SDKMod):
    Name: str = "Movement Tech"
    Description: str = "Enables slamming and double jumps for BL2."
    Author: str = "ZetaDæmon"
    Version: str = "1.0"
    SupportedGames = Game.BL2
    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadOnMainMenu

    Want_To_Slam: bool = False
    Slam_Speed = -6000
    Slam_Start_Height = 0
    Min_Slam_Height = 210
    Slam_Radius = 500
    Previous_Z = 0

    Base_Impact_Particles = [
        "FX_CHAR_Shared_Shield.Particles.Novas.Part_Incendiary_Nova_Shield_Explosion",
        "FX_CHAR_Shared_Shield.Particles.Novas.Part_Shock_Nova_Shield_Explosion",
        "FX_CHAR_Shared_Shield.Particles.Novas.Part_Explosive_Nova_Shield_Explosion",
        "FX_CHAR_Shared_Shield.Particles.Novas.Part_Corrosive_Nova_Shield_Explosion",
        "FX_CHAR_Shared_Shield.Particles.Novas.Part_Slag_Nova_Shield_Explosion"
    ]
    Custom_Impact_Particles = [
        "Slam_Custom_Fire",
        "Slam_Custom_Shock",
        "Slam_Custom_Explosive",
        "Slam_Custom_Corrosive",
        "Slam_Custom_Slag"
    ]
    Emmitter_Idx_Lists = [
        [2, 3, 4],
        [0, 2],
        [1],
        [1, 2],
        [0, 3],
    ]
    Impact_Sound = "Ake_Exp_Elemental.Exp_Explosive.Ak_Play_Exp_Elemental_Explosive_MED"
    Frame_Names = [
        "Fire",
        "shock",
        "explosive",
        "corrosive",
        "amp"
    ]
    Damage_Dict = {
        "Fire": "GD_Incendiary.DamageType.DmgType_Incendiary_Impact",
        "shock": "GD_Shock.DamageType.DmgType_Shock_Impact",
        "explosive": "GD_Explosive.DamageType.DmgType_Explosive_Impact",
        "corrosive": "GD_Corrosive.DamageType.DmgType_Corrosive_Impact",
        "amp": "GD_Amp.DamageType.DmgType_Amp_Impact"
    }
    Impact_Dict = {
        "Fire": "GD_Impacts.ExplosiveImpacts.ExplosiveImpactIncendiary128",
        "shock": "GD_Impacts.ExplosiveImpacts.ExplosiveImpactShock128",
        "explosive": "GD_Impacts.ExplosiveImpacts.ExplosiveImpactNormal128",
        "corrosive": "GD_Impacts.ExplosiveImpacts.ExplosiveImpactCorrosive128",
        "amp": "GD_Impacts.ExplosiveImpacts.ExplosiveImpactEridian128"
    }
    Particle_Dict = {}

    Wants_To_Double_Jump = False
    Double_Jumped = False
    Jump_Velocity = 420
    Jump_Sound = "Ake_Fs_Player.Ak_Play_Fs_Jump"

    def get_damage_type(self, framename) -> str:
        if framename in self.Frame_Names:
            return self.Damage_Dict[framename]
        return "GD_Explosive.DamageType.DmgType_Explosive_Impact"

    def get_explosion_impact(self, framename) -> str:
        if framename in self.Frame_Names:
            return self.Impact_Dict[framename]
        return "GD_Impacts.ExplosiveImpacts.ExplosiveImpactNormal128"

    def get_particle(self, framename) -> str:
        if framename in self.Frame_Names:
            return self.Particle_Dict[framename]
        return self.Particle_Dict["explosive"]

    def slam_damage(self, power) -> float:
        multiplier = 8
        level = unrealsdk.FindObject("ConstantAttributeValueResolver", "GD_Balance_HealthAndDamage.HealthAndDamage.Att_UniversalBalanceScaler:ConstantAttributeValueResolver_0").ConstantValue
        return multiplier * (pow(level, power))

    def clone_particle(self, src, new_name, emmitter_idx_list) -> unrealsdk.UObject:
        Base_Particle = unrealsdk.FindObject("ParticleSystem", src)
        template = Base_Particle.ObjectArchetype
        Custom_Impact_Particle = unrealsdk.ConstructObject(
            Class=Base_Particle.Class,
            Outer=Base_Particle.Outer,
            Name=new_name
            # Template=template
        )
        unrealsdk.KeepAlive(Custom_Impact_Particle)
        Custom_Impact_Particle.ObjectArchetype = Base_Particle.ObjectArchetype
        Custom_Impact_Particle.ObjectFlags.B |= 4

        Base_Emitters = Base_Particle.Emitters
        New_Emitters = []
        for idx in emmitter_idx_list:
            New_Emitters.append(Base_Emitters[idx])
        Custom_Impact_Particle.Emitters = New_Emitters
        return Custom_Impact_Particle

    def construct_particles(self):
        obj = unrealsdk.FindObject("ParticleSystem", "FX_CHAR_Shared_Shield.Particles.Novas.Part_Slag_Nova_Shield_Explosion")
        if not obj:
            unrealsdk.LoadPackage("Sage_Underground_Combat")
            obj = unrealsdk.FindObject("ParticleSystem", "FX_CHAR_Shared_Shield.Particles.Novas.Part_Slag_Nova_Shield_Explosion")
        unrealsdk.KeepAlive(obj)
        for idx in range(len(self.Base_Impact_Particles)):
            self.Particle_Dict[self.Frame_Names[idx]] = self.clone_particle(
                self.Base_Impact_Particles[idx],
                self.Custom_Impact_Particles[idx],
                self.Emmitter_Idx_Lists[idx]
            )

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

        is_grounded = pawn.IsOnGroundOrShortFall()
        if self.Want_To_Slam:
            # Check to make sure you dont get suck slamming but not registering on the ground
            if pawn.Location.Z == self.Previous_Z:
                is_grounded = True
            self.Previous_Z = pawn.Location.Z

            pawn.Velocity = self.Fall_Direction
            if is_grounded:
                self.Want_To_Slam = False
                falldistance = self.Slam_Start_Height - pawn.Location.Z
                if falldistance > self.Min_Slam_Height:
                    emitter_pool = unrealsdk.GetEngine().GetCurrentWorldInfo().MyEmitterPool
                    player_location = (pawn.Location.X, pawn.Location.Y, pawn.Location.Z)
                    damage_multiplier = 3 + 0.5 * falldistance / self.Min_Slam_Height
                    artifact = pawn.EquippedItems[3]
                    framename = artifact.GetElementalFrame()

                    emitter_pool.SpawnEmitter(self.get_particle(framename), player_location,)
                    pawn.PlayAkEvent(unrealsdk.FindObject("AkEvent", self.Impact_Sound))

                    pawn.Behavior_CauseRadiusDamage(
                        self.Slam_Radius,
                        damage_multiplier * self.slam_damage(pawn.GetExpLevel()),
                        True,
                        0,
                        unrealsdk.FindClass("DmgType_Crushed"),
                        unrealsdk.FindObject("WillowDamageTypeDefinition", self.get_damage_type(framename)),
                        unrealsdk.FindObject("WillowExplosionImpactDefinition", self.get_explosion_impact(framename)),
                        False
                    )

        if self.Wants_To_Double_Jump:
            self.Wants_To_Double_Jump = False
            self.Double_Jumped = True
            _x, _y = pawn.Velocity.X, pawn.Velocity.Y
            pawn.Velocity = (_x, _y, self.Jump_Velocity)
            pawn.PlayAkEvent(unrealsdk.FindObject("AkEvent", self.Jump_Sound))

        if self.Double_Jumped:
            if is_grounded:
                self.Double_Jumped = False

        return True

    def Enable(self) -> None:
        self.construct_particles()
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "TickPlayer",
                               lambda c, f, p: self.tick_player(c, f, p))
        unrealsdk.RegisterHook("WillowGame.WillowPlayerInput.DuckPressed", "SlamInputStart",
                               lambda c, f, p: self.start_slam(c, f, p))
        unrealsdk.RegisterHook("WillowGame.WillowPlayerInput.Jump", "Jumped",
                               lambda c, f, p: self.jump(c, f, p))

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "TickPlayer")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerInput.DuckPressed", "SlamInputStart")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerInput.Jump", "Jumped")


unrealsdk.RegisterMod(MovementTech())
