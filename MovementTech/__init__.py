import unrealsdk
from Mods.ModMenu import SDKMod, EnabledSaveType, ModTypes, Game, Options, Mods, RegisterMod, Hook
from Mods.ModMenu import ServerMethod, ClientMethod
from Mods.Enums import ENetMode, EModifierType

def is_client():
	return unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode == ENetMode.NM_Client

def get_pc() -> unrealsdk.UObject:
	return unrealsdk.GetEngine().GamePlayers[0].Actor


class MovementTech(SDKMod):
	Name: str = "Movement Tech"
	Description: str = "Enables slamming and double jumps for BL2.\nNow with multiplayer support!"
	Author: str = "ZetaDaemon"
	Version: str = "1.2"
	SupportedGames = Game.BL2
	Types: ModTypes = ModTypes.Gameplay
	SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadOnMainMenu

	slamming: bool = False
	slam_gravity = 29
	slam_radius = 500

	package = None
	gravity_attr = None
	gravity_modifier = None
	jump_attr = None
	jump_modifier = None
	
	players = {}

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
	Particle_Dict = {}

	can_double_jump = True
	Jump_Sound = "Ake_Fs_Player.Ak_Play_Fs_Jump"


	def __init__(self) -> None:
		self.JumpHeight = Options.Slider (
			Caption="Jump Height Increase",
			Description="Percent increase for jump height. (Dictated by host)",
			StartingValue=0,
			MinValue=0,
			MaxValue=100,
			Increment=1,
			IsHidden=False
		)
		self.Options = [
			self.JumpHeight
		]

	def get_damage_type(self, framename) -> str:
		if framename in self.Frame_Names:
			return self.Damage_Dict[framename]
		return "GD_Explosive.DamageType.DmgType_Explosive_Impact"

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
		Custom_Impact_Particle = unrealsdk.ConstructObject(
			Class=Base_Particle.Class,
			Outer=Base_Particle.Outer,
			Name=new_name
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
	
	def construct_attrs(self):
		self.package = unrealsdk.ConstructObject(
			Class="Package",
			Outer=None,
			Name="MovementTech",
		)
		unrealsdk.KeepAlive(self.package)
		self.gravity_attr = unrealsdk.ConstructObject(
			Class=unrealsdk.FindClass('AttributeDefinition'),
			Outer=self.package,
			Name='PawnGravity'
		)
		unrealsdk.KeepAlive(self.gravity_attr)
		self.gravity_attr.ContextResolverChain = [
			unrealsdk.ConstructObject(
				Class=unrealsdk.FindClass('PawnAttributeContextResolver'),
				Outer=self.gravity_attr,
				Name=''
			)
		]
		self.gravity_attr.ValueResolverChain = [
			unrealsdk.ConstructObject(
				Class=unrealsdk.FindClass('ObjectPropertyAttributeValueResolver'),
				Outer=self.gravity_attr,
				Name=''
			)
		]
		get_pc().ConsoleCommand(f"set {self.gravity_attr.PathName(self.gravity_attr.ValueResolverChain[0])} PropertyName CustomGravityScaling")
		self.gravity_modifier = unrealsdk.ConstructObject(
			Class="AttributeModifier",
			Outer=self.package,
			Name="GravityModifier"
		)
		unrealsdk.KeepAlive(self.gravity_modifier)
		self.gravity_modifier.Type = EModifierType.MT_Scale
		self.gravity_modifier.Value = self.slam_gravity

		self.jump_attr = unrealsdk.FindObject('AttributeDefinition', 'D_Attributes.GameplayAttributes.JumpHeight')
		self.jump_modifier = unrealsdk.ConstructObject(
			Class="AttributeModifier",
			Outer=self.package,
			Name="JumpModifier"
		)
		self.jump_modifier.Type = EModifierType.MT_Scale
		self.jump_modifier.Value = float(self.JumpHeight.CurrentValue/100)
		unrealsdk.KeepAlive(self.jump_modifier)
		
	def spawn_particle(self, framename, location):
		emitter_pool = unrealsdk.GetEngine().GetCurrentWorldInfo().MyEmitterPool
		emitter_pool.SpawnEmitter(self.get_particle(framename), tuple(location),)
	
	@ClientMethod
	def client_spawn_particle(self, framename, location):
		self.spawn_particle(framename, location)
	
	@ServerMethod
	def server_spawn_particle(self, framename, location):
		self.client_spawn_particle(framename, location)
		self.spawn_particle(framename, location)
	
	def apply_jump_modifier(self, pawn):
		self.jump_modifier.Value = float(self.JumpHeight.CurrentValue/100)
		self.jump_attr.AddAttributeModifier(pawn, self.jump_modifier)
	
	def remove_jump_modifier(self, pawn):
		self.jump_attr.RemoveAttributeModifier(pawn, self.jump_modifier)
	
	@ServerMethod
	def server_apply_jump_modifier(self, PC = None):
		self.apply_jump_modifier(PC.Pawn)
	
	def start_slam(self, PC):
		if PC not in self.players:
			self.players[PC] = True
		elif self.players[PC]:
			return
		self.players[PC] = True
		self.gravity_attr.AddAttributeModifier(PC.Pawn, self.gravity_modifier)
	
	@ServerMethod
	def server_start_slam(self, PC = None):
		if PC is not None:
			self.start_slam(PC)
	
	@Hook("WillowGame.WillowPlayerInput.DuckPressed")
	def try_slam(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
		PC = this.Outer
		if PC.Pawn.IsOnGroundOrShortFall():
			return True
		if is_client():
			self.server_start_slam()
		else:
			self.start_slam(PC)
		return False

	def handle_impact(self, velocity, PC):
		if PC not in self.players:
			self.players[PC] = False
		was_slamming = self.players[PC]
		if not was_slamming:
			return
		pawn = PC.Pawn

		self.gravity_attr.RemoveAttributeModifier(pawn, self.gravity_modifier)
		self.jump_attr.RemoveAttributeModifier(pawn, self.jump_modifier)
		self.players[PC] = False
		velocity*=-1
		if velocity < 4000:
			return True
		player_location = (pawn.Location.X, pawn.Location.Y, pawn.Location.Z-70)
		damage_multiplier = 3 + 0.5 * velocity / 4000
		artifact = pawn.EquippedItems[3]
		if artifact is not None:
			framename = artifact.GetElementalFrame()
		else:
			framename = "explosive"
		if is_client():
			self.server_spawn_particle(framename, player_location)
		else:
			self.client_spawn_particle(framename, player_location)
			self.spawn_particle(framename, player_location)
		pawn.PlayAkEvent(unrealsdk.FindObject("AkEvent", self.Impact_Sound))
		pawn.Behavior_CauseRadiusDamage(
			self.slam_radius,
			damage_multiplier * self.slam_damage(pawn.GetGameStage()),
			True,
			velocity*10,
			unrealsdk.FindClass("DmgType_Crushed"),
			unrealsdk.FindObject("WillowDamageTypeDefinition", self.get_damage_type(framename)),
			None,
			False
		)
	
	def server_handle_impact(self, velocity, PC = None):
		if PC is not None:
			self.handle_impact(velocity, PC)

	@Hook("WillowGame.WillowPlayerPawn.PlayLanded")
	def landed(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
		self.can_double_jump = True
		if is_client():
			self.server_handle_impact(params.ImpactVel)
		else:
			self.handle_impact(params.ImpactVel, this.Controller)
		return True
		
	
	@Hook("WillowGame.WillowPlayerPawn.DoJump")
	def try_jump(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
		if not self.can_double_jump:
			return True
		if this.CanJump():
			if is_client():
				self.server_apply_jump_modifier()
			else:
				self.apply_jump_modifier(this)
			return True
		self.can_double_jump = False
		this.Physics = 1
		return True

	def Enable(self) -> None:	
		super().Enable()
		self.construct_particles()
		self.construct_attrs()


instance = MovementTech()
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
