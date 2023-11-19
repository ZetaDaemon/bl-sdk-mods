# Better Damage Feedback
Allows for the customisation of damage particles changing the colour, colour on crit, toggle CRITICAL effect, increased size on crit or turn damage numbers off entirely. Additionally allows for hit sounds and critical hit sounds.

Adds support for other mods to give the information for damage particles by setting `use_custom_data_input` to True and then calling `display_damage_event(event: RecentDamage, PC: unrealsdk.UObject)` to display a particle with the given data.

### v1.0
Initial Release.
