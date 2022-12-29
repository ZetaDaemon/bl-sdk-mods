import unrealsdk
from Mods.ModMenu import ModTypes, RegisterMod, SDKMod, EnabledSaveType, Mods, Hook
from Mods.Enums import EInputEvent
from typing import List, Callable

# Allows other mods to set up conditions for being able to remove skills.
# unspec_condition will take the player controller and then the skill to be removed.
# unspec_condition must return a bool of true of false as to if the skill should be removed.
unspec_condition = Callable[[unrealsdk.UObject, unrealsdk.UObject], bool]

unspec_conditions: List[unspec_condition] = []

def add_unspec_conditions(Condition: unspec_condition):
	unspec_conditions.append(Condition)

def remove_unspec_conditions(Condition: unspec_condition):
	unspec_conditions.remove(Condition)

class UnspecSkills(SDKMod):
	Name: str = "Unspec Skills"
	Author: str = "ZetaDaemon"
	Description: str = "Allows you to unspec skills by right clicking on them, as long as your other specced skills allow it."
	Version: str = "1.0"
	Types: ModTypes = ModTypes.Gameplay
	SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

	def can_remove_point(self, PC: unrealsdk.UObject, Tree: unrealsdk.UObject, Branch: int, Skill: unrealsdk.UObject) -> bool:
		for Condition in unspec_conditions:
			if not Condition(PC, Skill):
				return False

		points = 0
		for Tier in Tree.Tiers:
			if Tier.ParentBranchIndex != Branch:
				continue
			TierPoints = 0
			for idx in Tier.SkillIndices:
				TierPoints += PC.GetSkillGrade(Tree.Skills[idx].Definition)
			if points < (Tier.BranchPointsToUnlockTier) and TierPoints > 0:
				return False
			points += TierPoints
		return True
	
	def update_tree_progression(self, PC: unrealsdk.UObject, Tree: unrealsdk.UObject):
		points = 0
		branch = 0
		for Tier in Tree.Tiers:
			if Tier.ParentBranchIndex == 0:
				continue
			if branch != Tier.ParentBranchIndex:
				points = 0
				branch = Tier.ParentBranchIndex
			if points < (Tier.BranchPointsToUnlockTier):
				Tier.bUnlocked = False
			else:
				Tier.bUnlocked = True
			for idx in Tier.SkillIndices:
				points += PC.GetSkillGrade(Tree.Skills[idx].Definition)

	def Enable(self):
		@Hook("WillowGame.SkillTreeGFxObject.HandleInputKey", "UnspecSkills")
		def handle_input_key(this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
			if not params.uevent == EInputEvent.IE_Pressed:
				return True
			if not params.ukey == "RightMouseButton":
				return True
			
			# Since right click is now a proper action we need to make sure to set the selected skill to the one being hovered over
			old_skill = this.CurrentSkill
			this.CurrentSkill = this.CurrentSkill_Rollover
			this.PostNav(old_skill, 4)

			# Gets current branch excluding the action skill branch which is actually branch 0, hence the +1
			branch = this.GetEffectiveCurrentBranchNumber()
			branch += 1

			PC = this.WPCOwner
			skill = this.CurrentSkill
			grade = PC.GetSkillGrade(skill)
			if grade == 0:
				this.Movie.PlaySpecialUISound("ResultFailure")
				return True
			cost = PC.GetSkillUpgradeCost(skill)
			grade -= 1
			PC.PlayerSkillTree.SetSkillGrade(skill, grade)
			if not self.can_remove_point(PC, PC.PlayerSkillTree, branch, skill):
				PC.PlayerSkillTree.SetSkillGrade(skill, grade+1)
				this.Movie.PlaySpecialUISound("ResultFailure")
				return True

			# Updates a skill to the new grade level
			PC.GetSkillManager().UpdateSkillGrade(PC, skill, grade)
			# Returns the number of points the skill costed (Normally 1 but mods can change this)
			PC.PlayerReplicationInfo.GeneralSkillPoints += cost
			# Need to deactivate the skill instance if the grade reaches 0
			if grade == 0:
				PC.GetSkillManager().DeactivateSkill(PC, skill)

			# Lock skills if theyre no longer available
			self.update_tree_progression(PC, PC.PlayerSkillTree)

			# Bunch of engine functions that make the UI work (Honestly just guessed since part of the engine stuff is hidden, just called what seems right)
			this.HandleSkillPointsChange(this.NumSkillPoints + cost)
			this.Flash_SendInitialSkillData()
			this.UpdateSkillIcon(skill)
			this.CalculateBranchProgression()
			this.UpdateInfoBox()
			PC.PlayerSkillTree.UpdateBranchProgression(this)

			# Plays the buy point sound for the grade you just removed
			this.Movie.PlayUISound(f'BuyPoint{grade+1}')
			return True


instance = UnspecSkills()
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
