Little Thunder
===

Welcome! This is my bot, Little Thunder. He's a tabletop RPG utility bot for use with Discord, mostly designed around Play-by-Post styled games. Below, I'll give an overview of the command groups you can use with him.

Dice
---
Dice are an integral part to the majority of tabletop RPGs. While Little Thunder's dice are simple now, improvements are planned, and will be kept up to date here.

There is only a single command surrounding the use of dice, which is `.[d|dice|r|roll]`. This command's syntax is fairly simple, following `XdX` notation seen standard in many games. You can add and subtract both dice expressions and flat numbers to your initlal dice.

This will look something like `.d 1d20+12+2d6` in practice. If you wish to label your roll, you can follow your dice expression with `#` and anything that follows it will be added to the dice output as a label.

DM
---

The `.dm` family of commands is very simple; there are only two subcommands.

`.dm [register|add]` is the first subcommand, which sets the user who initiates the command as the Owner for the category of channels that the command is used within.

`.dm [unregister|remove]` is the other, which can be used by either the existing DM for a category or an administrator, and removes the user as a registered DM.

Initiative Tracker
---

Next, we've got our initiative tracking. These are handled by the `.init` command group. In order for all functionality to be available, there must be a DM assigned to the category you wish to use Initiative Tracking within.

The `.init` command itself will show a snapshot of the current initiative table. All combatants will be listed, with the person whose turn is currently active appearing at the top of the list, and working forward from there.

`.init [show|display]` works very similarly to the base command, but also pings the user who's turn is currently active.

`.init [new|add]` is how combatants are added to the initiative table, and there are two ways to use it. 

The first is to set the initiative value manually, done by following `.init new` with a name and an initiative value, such as `.init new Anton 15`. This would set Anton to an initiative value of 15 in the current tracker.

This command can also be used with dice, rolling automatically and placing the outcome into the initiative table, by using almost identical syntax: `.init new Anton 1d20` will roll a 20-sided die, and place Anton at the initiative value which is rolled.

Regardless of the method used to set initiative values, you can also assign combatants to another user by following the command with a mentioned user.

`.init [kill|remove]` is the command used to remove a character from the initiative table. This is done by following the command with the name of the combatant you wish to be removed, and is only usable by the DM of the category.

`.init [next|pass]` is the command used by a player or DM to signal that their turn is complete. This cycles the initiative table so that the next combatant is shown at the top, and the user who the combatant belongs to is pinged.

`.init delay` is a command which moves the current combatant to a new initiative value, which is simply used by appending a number value to the end of the command.

`.init end` is used to end a combat. This simply wipes the initiative table clean so that the manual removal of combatants is not required.

Character Profiles
---

The final command group which Little Thunder has is the Character Profile command group, shortened to `.char`. These are largely a vanity item, but the character profile can have any fields added a user might want. Moving forward, there are plans for more useful portions of this, but for now there's not much by way of a use case or function for these.

`.char add` is used to add a character to a server's character database, performed by appending the character's name to the end of the command.

`.char remove`, as one might expect, does the opposite, removing the named character from the database. This can only be performed by the owner of a character.

`.char [addfield|set]` is used to add a field to a character's profile, or update an existing field. This is done by appending a character's name and the fieldname to the command, followed by whatever content you may wish to have stored in the field. The storage limit of a discord embed's field is 2000 characters, and the total length limit for an embed is 8000 characters, so don't keep things too long.

In addition to text or number values, there are a few fields you can set a little more specifically.

`.char set <name> color <int>` is used to set the color of your embed's sidebar, and accepts a 6 digit hexadecimal number which refers to a color.

`.char set <name> image <img url>` is used to show character art, or something similar, below any text/number entries on the embed, and accepts a URL to an image.

`.char set <name> token <img url>` is used to show a token-sized thumbnail in the upper right-hand corner of your character's embed, and also accepts a URL.

`.char [removefield|unset]` does the opposite, removing a field from an existing character.

`.char display` uses the Database object stored for a character to display an embed of that character, with all non-backend fields shown.

The final command for the character group is `.char webedit`. This command does very little, aside from redirect the user to the Little Thunder Web Editor, called WebThunder.

Miscellaneous
---

In addition to these Tabletop RPG functions, there are a handful of additional things Little Thunder can perform.

The `.[purge|clear|p]` command, for instance, can purge posts made, filtering by user or by keyword. This requires `manage_messages` permission level on the activating user, and is used as follows.

`.purge 20` removes the last 20 messages, regardless of content or sender.  
`.purge 20 @CaydenCailean#6438` removes any messages within the last 20 which were sent by the user CaydenCailean#6438.  
`.purge 20 everyone foo` removes any messages within the last 20 which contain the keyword `foo`.  
These commands can be combined to purge only messages from a specific user that mention a keyword.

There are 3 more bot-centric commands, as well.

`.info` is probably how you got here in the first place, providing some basic information about the bot, a link to our donation page, and the github you see here.

`.suggest` is a command which sends the content following it to a server of mine where I can sort through the suggestions myself.

`.bugreport` is a very similar command to the above, but is sent to a dedicated bug report channel.

Closing Remarks
===

Thank you, again, for using Little Thunder! We greatly appreciate any bug reports or suggestions our users have to offer, and hope that you will get plenty of use out of what's been a very fulfilling project to work on!

If you have any questions which need to be answered, feel free to DM me on Discord; my username is `@Cayden Cailean#6438`, and I'm usually happy to help with any issues or just talk to someone who's got feedback about the bot, good or bad!