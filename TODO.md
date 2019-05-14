# INTFICPY - Write Parser Based Interactive Fiction in Python
IntFicPy is a tool for building parser based interactive fiction using Python. Currently, IntFicPy is in preparation for the first Beta release. A demo game, planned to be released for IFComp 2019, is in early development.

## KNOWN BUGS (Immediate Priority)
### Saving
+ default save location should be home folder
### Serializer
+ conversation topics, creator-defined variables, and player knowledge are not currently saved
+ check validity of save file before trying to load
### Terminal Mode
+ some non graphical features may not be available in terminal mode

## FEATURES THAT REQUIRE TESTING
+ make sure the search function finds all Things in the location/inventory
+ the [MORE] or <<e>> built in inline function needs more testing
+ test thing.copyThing with saving and loading
+ the describeThing and xdescribeThing methods of Thing

##  PREPARATIONS FOR FIRST BETA (Upcoming Features)
### Convenience & Ease of Use
+ write script to ensure game creator compliance with IntFicPy rules and syntax
+ implicit doff, implicit take, implicit drop
+ work on interactivity range
### Essential New Features
+ display the game title in the GUI window title
+ make the player interactable
+ give/show topics
+ interactable walls
+ Abstract class - Things referring to ideas and concepts
### Other New Features
+ support multiple Player characters
+ compound Things
+ allow game creators to modify the look of the GUI from within the main gamefile

## MAJOR CHANGES (Eventual Implementation)
+ Rewrite GUI with a different GUI module (currently using Qt)

## LAST DOCUMENTATION UPDATE COMPLETED: 29/04/2019
(X) actor.py
(X) parser.py
(X) thing.py
(X) vocab.py
(X) gui.py
(X) player.py
(X) room.py
(X) travel.py
(X) serializer.py
(X) verb.py