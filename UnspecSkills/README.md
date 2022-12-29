# Unspec Skills
Allows you to right click on skills to remove points from them. Removing points does get restricted by having points further up in the tree meaning you cannot go unlock a later skill and then just remove points from early skills.

You will need to download [Enums](https://bl-sdk.github.io/mods/Enums/) for this to work.

## Custom Unspec Conditions
Other mods can add custom conditions for being able to unspec skills, to do this you need a function that takes 2 `unrealsdk.UObject` arguments and then returns true or false. The 2 arguments are the `WillowPlayerController` trying to remove points and then the `SkillDefinition` that the player is trying to remove.
```py
def unspec_condition(PC: unrealsdk.UObject, Skill: unrealsdk.UObject) -> bool:
	# Do Check
	return True
```

### v1.0
Initial Release.