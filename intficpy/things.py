import copy

from .vocab import nounDict
from .actor import Actor, Player
from .thing_base import Thing


class Surface(Thing):
    """Class for Things that can have other Things placed on them """

    def __init__(self, name, me):
        """Sets the essential properties for a new Surface object """
        super().__init__(name)

        self._me = me
        self.contains_preposition = "on"
        self.contains_on = True
        self.contains_preposition_inverse = "off"

        self.canSit = False
        self.canStand = False
        self.canLie = False

        self.desc_reveal = True

    def containsListUpdate(self, update_desc=True, update_xdesc=True):
        """Update description of contents
		Called when a Thing is added or removed """
        onlist = " On the " + self.name + " is "
        if update_desc:
            self.compositeBaseDesc()
        if update_xdesc:
            self.compositeBasexDesc()
        # iterate through contents, appending the verbose_name of each to onlist
        list_version = list(self.contains.keys())
        player_here = False
        for key in list_version:
            for item in self.contains[key]:
                if isinstance(item, Player):
                    list_version.remove(key)
                    player_here = True
                elif item.parent_obj:
                    list_version.remove(key)
        for key in list_version:
            if len(self.contains[key]) > 1:
                onlist = (
                    onlist + str(len(things)) + " " + self.contains[key][0].getPlural()
                )
            else:
                onlist = (
                    onlist
                    + self.contains[key][0].getArticle()
                    + self.contains[key][0].verbose_name
                )
            if key is list_version[-1]:
                onlist = onlist + "."
            elif key is list_version[-2]:
                onlist = onlist + " and "
            else:
                onlist = onlist + ", "
            if key not in self._me.knows_about:
                self._me.knows_about.append(key)
        # if contains is empty, there should be no onlist
        # TODO: consider rewriting this logic to avoid contructing an empty onlist, then deleting it
        if len(list_version) == 0:
            onlist = ""
        if player_here:
            if onlist != "":
                onlist = onlist + "<br>"
            onlist = (
                onlist + "You are on " + self.getArticle(True) + self.verbose_name + "."
            )
        # append onlist to description
        if self.is_composite:
            if self.children_desc:
                self.desc = self.desc + self.children_desc
                self.xdesc = self.xdesc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.xdesc = self.xdesc + item.desc
                    self.desc = self.desc + item.desc
            if self.desc_reveal and update_desc:
                self.desc = self.desc + onlist
            if update_xdesc:
                self.xdesc = self.xdesc + onlist
        else:
            if self.desc_reveal and update_desc:
                self.desc = self.base_desc + onlist
            if update_xdesc:
                self.xdesc = self.base_xdesc + onlist
        self.contains_desc = onlist

    def addThing(self, item):
        """Add a Thing to a Surface
		Takes argument item, pointing to a Thing"""
        if isinstance(item, Container):
            if item.lock_obj and (
                item.lock_obj.ix in self.contains
                or item.lock_obj.ix in self.sub_contains
            ):
                if not (
                    item.lock_obj in self.contains[item.lock_obj.ix]
                    or item.lock_obj in self.sub_contains[item.lock_obj.ix]
                ):
                    self.addThing(item.lock_obj)
            elif item.lock_obj:
                self.addThing(item.lock_obj)
        if item.is_composite:
            for item2 in item.children:
                if item2.ix in self.contains:
                    if not item2 in self.contains[item2.ix]:
                        self.addThing(item2)
                else:
                    self.addThing(item2)
        item.location = self
        # nested items
        nested = getNested(item)
        next_loc = self.location
        while next_loc:
            if not isinstance(item, Actor):
                for t in nested:
                    if t.ix in next_loc.sub_contains:
                        if not t in next_loc.sub_contains[t.ix]:
                            next_loc.sub_contains[t.ix].append(t)
                    else:
                        next_loc.sub_contains[t.ix] = [t]
            if item.ix in next_loc.sub_contains:
                if not item in next_loc.sub_contains[item.ix]:
                    next_loc.sub_contains[item.ix].append(item)
            else:
                next_loc.sub_contains[item.ix] = [item]
            next_loc = next_loc.location
        for t in nested:
            if not isinstance(item, Actor):
                if t.ix in self.sub_contains:
                    self.sub_contains[t.ix].append(t)
                else:
                    self.sub_contains[t.ix] = [t]
        # top level item
        if item.ix in self.contains:
            self.contains[item.ix].append(item)
        else:
            self.contains[item.ix] = [item]
        if item.ix in self.location.sub_contains:
            self.location.sub_contains[item.ix].append(item)
        else:
            self.location.sub_contains[item.ix] = [item]
        self.containsListUpdate()

    def removeThing(self, item, update_desc=True, update_xdesc=True):
        """Remove a Thing from a Surface """
        if isinstance(item, Container):
            if item.lock_obj:
                if item.lock_obj.ix in self.contains:
                    if item.lock_obj in self.contains[item.lock_obj.ix]:
                        self.removeThing(item.lock_obj)
                if item.lock_obj.ix in self.sub_contains:
                    if item.lock_obj in self.sub_contains[item.lock_obj.ix]:
                        self.removeThing(item.lock_obj)
        if item.is_composite:
            for item2 in item.children:
                if item2.ix in self.contains:
                    if item2 in self.contains[item2.ix]:
                        self.removeThing(item2)
                if item2.ix in self.sub_contains:
                    if item2 in self.sub_contains[item2.ix]:
                        self.removeThing(item2)
        nested = getNested(item)
        for t in nested:
            if t.ix in self.sub_contains:
                if t in self.sub_contains[t.ix]:
                    self.sub_contains[t.ix].remove(t)
                    if self.sub_contains[t.ix] == []:
                        del self.sub_contains[t.ix]
        next_loc = self.location
        while next_loc:
            if item.ix in next_loc.sub_contains:
                if item in next_loc.sub_contains[item.ix]:
                    next_loc.sub_contains[item.ix].remove(item)
                    if next_loc.sub_contains[item.ix] == []:
                        del next_loc.sub_contains[item.ix]
            for t in nested:
                if t.ix in next_loc.sub_contains:
                    if t in next_loc.sub_contains[t.ix]:
                        next_loc.sub_contains[t.ix].remove(t)
                        if next_loc.sub_contains[t.ix] == []:
                            del next_loc.sub_contains[t.ix]
            next_loc = next_loc.location
        rval = False
        if item.ix in self.contains:
            if item in self.contains[item.ix]:
                self.contains[item.ix].remove(item)
                if self.contains[item.ix] == []:
                    del self.contains[item.ix]
                rval = True
                item.location = False
                self.containsListUpdate(update_desc, update_xdesc)
        if item.ix in self.sub_contains:
            if item in self.sub_contains[item.ix]:
                self.sub_contains[item.ix].remove(item)
                if self.sub_contains[item.ix] == []:
                    del self.sub_contains[item.ix]
                rval = True
                item.location = False
                self.containsListUpdate(update_desc, update_xdesc)
        return rval

    def compositeBaseDesc(self):
        if self.is_composite:
            if self.children_desc:
                self.desc = self.base_desc + self.children_desc
            else:
                self.desc = self.base_desc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        else:
            self.desc = self.base_desc

    def compositeBasexDesc(self):
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                self.xdesc = self.base_xdesc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        else:
            self.xdesc = self.base_xdesc

    def describeThing(self, description):
        self.base_desc = description
        if self.is_composite:
            if self.children_desc:
                self.desc = self.base_desc + self.children_desc
            else:
                self.desc = self.base_desc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        self.containsListUpdate()

    def xdescribeThing(self, description):
        self.base_xdesc = description
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                self.xdesc = self.base_xdesc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        self.containsListUpdate()


# NOTE: Container duplicates a lot of code from Surface. Consider a parent class for Things with a contains property
class Container(Thing):
    """Things that can contain other Things """

    def __init__(self, name, me):
        """
        Set basic properties for the Container instance
        Takes argument name, a single noun (string)
        """
        super().__init__(name)
        self.size = 50
        self.desc_reveal = True
        self.xdesc_reveal = True
        self.contains_preposition = "in"
        self.contains_in = True
        self.contains_preposition_inverse = "out"

        self._me = me

    def updateDesc(self):
        self.containsListUpdate(True, True)

    def containsListUpdate(self, update_desc=True, update_xdesc=True):
        """Update description for addition/removal of items from the Container instance """
        from .actor import Player

        # desc = self.base_desc
        # xdesc = self.base_xdesc
        if update_desc:
            self.compositeBaseDesc()
        if update_xdesc:
            self.compositeBasexDesc()
        desc = self.desc
        xdesc = self.xdesc
        if self.has_lid:
            desc = desc + self.state_desc
            xdesc = xdesc + self.state_desc
            if not self.is_open:
                self.desc = desc
                self.xdesc = xdesc + self.lock_desc
                self.contains_desc = (
                    "You cannot see inside "
                    + self.getArticle(True)
                    + self.verbose_name
                    + " as it is closed."
                )
                return False
        inlist = " In the " + self.name + " is "
        # iterate through contents, appending the verbose_name of each to onlist
        list_version = list(self.contains.keys())
        player_here = False
        for key in list_version:
            for item in self.contains[key]:
                if isinstance(item, Player):
                    list_version.remove(key)
                    player_here = True
                elif item.parent_obj:
                    list_version.remove(key)
        for key in list_version:
            if len(self.contains[key]) > 1:
                inlist = (
                    inlist + str(len(things)) + " " + self.contains[key][0].verbose_name
                )
            else:
                inlist = (
                    inlist
                    + self.contains[key][0].getArticle()
                    + self.contains[key][0].verbose_name
                )
            if key is list_version[-1]:
                inlist = inlist + "."
            elif key is list_version[-2]:
                inlist = inlist + " and "
            else:
                inlist = inlist + ", "
            if key not in self._me.knows_about:
                self._me.knows_about.append(key)
        # remove the empty inlist in the case of no contents
        # TODO: consider rewriting this logic to avoid contructing an empty inlist, then deleting it
        if len(list_version) == 0:
            inlist = ""
        if player_here:
            if inlist != "":
                inlist = inlist + "<br>"
            inlist = (
                inlist + "You are in " + self.getArticle(True) + self.verbose_name + "."
            )
        # update descriptions
        if self.is_composite:
            if self.children_desc:
                self.desc = self.base_desc + self.children_desc
                self.xdesc = self.base_xdesc + self.children_desc
            else:
                self.xdesc = self.base_xdesc
                self.desc = self.base_desc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.xdesc = self.xdesc + item.desc
                    self.desc = self.desc + item.desc
            if update_desc and self.desc_reveal:
                self.desc = self.desc + inlist
            if update_xdesc and self.xdesc_reveal:
                self.xdesc = self.xdesc + inlist
        else:
            if update_desc and self.desc_reveal:
                self.desc = self.desc + inlist
            if update_xdesc and self.xdesc_reveal:
                self.xdesc = self.xdesc + self.lock_desc + inlist
        self.contains_desc = inlist
        return True

    def compositeBaseDesc(self):
        if self.is_composite:
            if self.children_desc:
                self.desc = self.base_desc + self.children_desc
            else:
                self.desc = self.base_desc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        else:
            self.desc = self.base_desc

    def compositeBasexDesc(self):
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                self.xdesc = self.base_xdesc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        else:
            self.xdesc = self.base_xdesc

    def addThing(self, item, update_desc=True, update_xdesc=True):
        """Add an item to contents, update descriptions
		Takes argument item, pointing to a Thing """

        item.location = self
        if isinstance(item, Container):
            if item.lock_obj and (
                item.lock_obj.ix in self.contains
                or item.lock_obj.ix in self.sub_contains
            ):
                if not (
                    item.lock_obj in self.contains[item.lock_obj.ix]
                    or item.lock_obj in self.sub_contains[item.lock_obj.ix]
                ):
                    self.addThing(item.lock_obj)
            elif item.lock_obj:
                self.addThing(item.lock_obj)
        if item.is_composite:
            for item2 in item.children:
                if item2.ix in self.contains:
                    if not item2 in self.contains[item2.ix]:
                        self.addThing(item2)
                else:
                    self.addThing(item2)
        # nested items
        nested = getNested(item)
        next_loc = self.location
        while next_loc:
            if not isinstance(item, Actor):
                for t in nested:
                    if t.ix in next_loc.sub_contains:
                        if not t in next_loc.sub_contains[t.ix]:
                            next_loc.sub_contains[t.ix].append(t)
                    else:
                        next_loc.sub_contains[t.ix] = [t]
            if item.ix in next_loc.sub_contains:
                if not item in next_loc.sub_contains[item.ix]:
                    next_loc.sub_contains[item.ix].append(item)
            else:
                next_loc.sub_contains[item.ix] = [item]
            next_loc = next_loc.location
        if not isinstance(item, Actor):
            for t in nested:
                if t.ix in self.sub_contains:
                    self.sub_contains[t.ix].append(t)
                else:
                    self.sub_contains[t.ix] = [t]
        if item.ix in self.contains:
            self.contains[item.ix].append(item)
        else:
            self.contains[item.ix] = [item]
        if self.has_lid:
            if not self.is_open:
                self.hideContents()
        self.containsListUpdate(update_desc, update_xdesc)

    def revealContents(self):
        list_version = list(self.contains.keys())
        for key in list_version:
            for item in self.contains[key]:
                nested = getNested(item)
                next_loc = self.location
                while next_loc:
                    for x in nested:
                        if x.ix in next_loc.sub_contains:
                            next_loc.sub_contains[x.ix].append(x)
                        else:
                            next_loc.sub_contains[x.ix] = [x]
                    if item.ix in next_loc.sub_contains:
                        next_loc.sub_contains[item.ix].append(item)
                    else:
                        next_loc.sub_contains[item.ix] = [item]
                    next_loc = next_loc.location

    def hideContents(self):
        list_version = list(self.contains.keys())
        for key in list_version:
            for item in self.contains[key]:
                nested = getNested(item)
                next_loc = self.location
                while next_loc:
                    for x in nested:
                        if x.ix in next_loc.sub_contains:
                            next_loc.sub_contains[x.ix].remove(x)
                            if next_loc.sub_contains[x.ix] == []:
                                del next_loc.sub_contains[x.ix]
                    if item.ix in next_loc.sub_contains:
                        next_loc.sub_contains[item.ix].remove(item)
                        if next_loc.sub_contains[item.ix] == []:
                            del next_loc.sub_contains[item.ix]
                    next_loc = next_loc.location

    def removeThing(self, item, update_desc=True, update_xdesc=True):
        """Remove an item from contents, update decription """
        if isinstance(item, Container):
            if item.lock_obj:
                if item.lock_obj.ix in self.contains:
                    if item.lock_obj in self.contains[item.lock_obj.ix]:
                        self.removeThing(item.lock_obj)
                if item.lock_obj.ix in self.sub_contains:
                    if item.lock_obj in self.sub_contains[item.lock_obj.ix]:
                        self.removeThing(item.lock_obj)
        if item.is_composite:
            for item2 in item.children:
                if item2.ix in self.contains:
                    if item2 in self.contains[item2.ix]:
                        self.removeThing(item2)
                if item2.ix in self.sub_contains:
                    if item2 in self.sub_contains[item2.ix]:
                        self.removeThing(item2)
        nested = getNested(item)
        for t in nested:
            if t.ix in self.sub_contains:
                if t in self.sub_contains[t.ix]:
                    self.sub_contains[t.ix].remove(t)
                    if self.sub_contains[t.ix] == []:
                        del self.sub_contains[t.ix]
        next_loc = self.location
        while next_loc:
            if item.ix in next_loc.sub_contains:
                if item in next_loc.sub_contains[item.ix]:
                    next_loc.sub_contains[item.ix].remove(item)
                    if next_loc.sub_contains[item.ix] == []:
                        del next_loc.sub_contains[item.ix]
            for t in nested:
                if t.ix in next_loc.sub_contains:
                    if t in next_loc.sub_contains[t.ix]:
                        next_loc.sub_contains[t.ix].remove(t)
                        if next_loc.sub_contains[t.ix] == []:
                            del next_loc.sub_contains[t.ix]
            next_loc = next_loc.location
        rval = False
        if item.ix in self.contains:
            if item in self.contains[item.ix]:
                self.contains[item.ix].remove(item)
                if self.contains[item.ix] == []:
                    del self.contains[item.ix]
                rval = True
                item.location = False
                self.containsListUpdate(update_desc, update_xdesc)
        if item.ix in self.sub_contains:
            if item in self.sub_contains[item.ix]:
                self.sub_contains[item.ix].remove(item)
                if self.sub_contains[item.ix] == []:
                    del self.sub_contains[item.ix]
                rval = True
                item.location = False
                self.containsListUpdate(update_desc, update_xdesc)
        return rval

    def setLock(self, lock_obj):
        if isinstance(lock_obj, Lock) and self.has_lid:
            if not lock_obj.parent_obj:
                self.lock_obj = lock_obj
                lock_obj.parent_obj = self
                self.location.addThing(lock_obj)
                lock_obj.setAdjectives(
                    lock_obj.adjectives + self.adjectives + [self.name]
                )
                if lock_obj.is_locked:
                    self.lock_desc = " It is locked. "
                else:
                    self.lock_desc = " It is unlocked. "
                lock_obj.describeThing("")
                lock_obj.xdescribeThing(
                    "You notice nothing remarkable about "
                    + lock_obj.getArticle(True)
                    + lock_obj.verbose_name
                    + ". "
                )
                self.containsListUpdate()
            else:
                print(
                    "Cannot set lock_obj for "
                    + self.verbose_name
                    + ": lock_obj.parent already set "
                )
        else:
            print("Cannot set lock_obj for " + self.verbose_name + ": not a Lock ")

    def containsLiquid(self):
        """Returns  the first Liquid found in the Container or None"""
        for key in self.contains:
            for item in self.contains[key]:
                if isinstance(item, Liquid):
                    return item
        return None

    def liquidRoomLeft(self):
        """Returns the portion of the Container's size not taken up by a liquid"""
        liquid = self.containsLiquid()
        if not liquid:
            return self.size
        return self.size - liquid.size

    def describeThing(self, description):
        self.base_desc = description
        self.desc = self.base_desc + self.state_desc
        if self.is_composite:
            if self.children_desc:
                self.desc = self.desc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        self.containsListUpdate()

    def xdescribeThing(self, description):
        self.base_xdesc = description
        self.xdesc = self.base_xdesc + self.state_desc + self.lock_desc
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.xdesc = self.xdesc + item.desc
        self.containsListUpdate()

    def giveLid(self):
        self.has_lid = True
        self.is_open = False
        self.state_desc = " It is currently closed. "
        self.containsListUpdate()

    def makeOpen(self):
        self.is_open = True
        self.state_desc = " It is currently open. "
        self.containsListUpdate()
        self.revealContents()
        if self.parent_obj:
            self.parent_obj.describeThing(self.parent_obj.base_desc)
            self.parent_obj.xdescribeThing(self.parent_obj.base_xdesc)

    def makeClosed(self):
        self.is_open = False
        self.state_desc = " It is currently closed. "
        self.containsListUpdate()
        self.hideContents()
        if self.parent_obj:
            self.parent_obj.describeThing(self.parent_obj.base_desc)
            self.parent_obj.xdescribeThing(self.parent_obj.base_xdesc)


# NOTE: May not be necessary as a distinct class. Consider just using the wearable property.
class Clothing(Thing):
    """Class for Things that can be worn """

    # all clothing is wearable
    wearable = True
    # uses __init__ from Thing


class LightSource(Thing):
    """Class for Things that are light sources """

    def __init__(self, name):
        """
        Set basic properties for the LightSource instance
        Takes argument name, a single noun (string)
        """
        super().__init__(name)

        self.base_desc = "There is " + self.getArticle() + self.verbose_name + " here. "
        self.base_xdesc = self.base_desc
        self.desc = self.base_desc + "It is currently not lit. "
        self.xdesc = self.base_xdesc + "It is currently not lit. "

        # LightSource properties
        self.is_lit = False
        self.player_can_light = True
        self.player_can_extinguish = True
        self.consumable = False
        self.turns_left = 20
        self.room_lit_msg = "The " + self.name + " lights your way. "
        self.light_msg = "You light the " + self.name + ". "
        self.already_lit_msg = "The " + self.name + " is already lit. "
        self.extinguish_msg = "You extinguish the " + self.name + ". "
        self.already_extinguished_msg = "The " + self.name + " is not lit. "
        self.cannot_light_msg = "You cannot light the " + self.name + ". "
        self.cannot_extinguish_msg = "You cannot extinguish the " + self.name + ". "
        self.cannot_light_expired_msg = "The " + self.name + " is used up. "
        self.extinguishing_expired_msg = (
            "The light of the " + self.name + " dims to nothing. "
        )
        self.expiry_warning = "The " + self.name + " flickers. "
        self.lit_desc = "It is currently lit. "
        self.not_lit_desc = "It is currently not lit. "
        self.expired_desc = "It is burnt out. "

    def describeThing(self, description):
        self.base_desc = description
        if self.is_lit:
            self.desc = self.base_desc + self.lit_desc
        elif self.consumable and not self.turns_left:
            self.desc = self.base_desc + self.expired_desc
        else:
            self.desc = self.base_desc + self.not_lit_desc

    def xdescribeThing(self, description):
        self.base_xdesc = description
        if self.is_lit:
            self.xdesc = self.base_xdesc + self.lit_desc
        elif self.consumable and not self.turns_left:
            self.xdesc = self.base_xdesc + self.expired_desc
        else:
            self.xdesc = self.base_xdesc + self.not_lit_desc

    def light(self, app):
        if self.is_lit:
            app.printToGUI(self.already_lit_msg)
            return True
        elif self.consumable and not self.turns_left:
            app.printToGUI(self.cannot_light_expired_msg)
            return False
        else:
            if self.consumable:
                # add the consumeLightSource daemon
                from .parser import daemons

                daemons.add(self.consumeLightSourceDaemon)
            self.is_lit = True
            self.desc = self.base_desc + self.lit_desc
            self.xdesc = self.base_xdesc + self.lit_desc

    def extinguish(self, app):
        if not self.is_lit:
            app.printToGUI(self.already_extinguished_msg)
            return True
        else:
            if self.consumable:
                # remove the consumeLightSource daemon
                from .parser import daemons

                if self.consumeLightSourceDaemon in daemons.funcs:
                    daemons.remove(self.consumeLightSourceDaemon)
            self.is_lit = False
            self.desc = self.base_desc + self.not_lit_desc
            self.xdesc = self.base_xdesc + self.not_lit_desc

    def consumeLightSourceDaemon(self, me, app):
        """Runs every turn while a consumable light source is active, to keep track of time left. """
        from .parser import lastTurn, daemons
        from .verb import helpVerb, helpVerbVerb, aboutVerb

        if not (
            lastTurn.verb == helpVerb
            or lastTurn.verb == helpVerbVerb
            or lastTurn.verb == aboutVerb
            or lastTurn.ambiguous
            or lastTurn.err
        ):
            self.turns_left = self.turns_left - 1
            if self.turns_left == 0:
                if me.getOutermostLocation() == self.getOutermostLocation():
                    app.printToGUI(self.extinguishing_expired_msg)
                self.is_lit = False
                self.desc = self.base_desc + self.expired_desc
                self.xdesc = self.base_xdesc + self.expired_desc
                if self.consumeLightSourceDaemon in daemons.funcs:
                    daemons.remove(self.consumeLightSourceDaemon)
            elif me.getOutermostLocation() == self.getOutermostLocation():
                if self.turns_left < 5:
                    app.printToGUI(
                        self.expiry_warning + str(self.turns_left) + " turns left. "
                    )
                elif (self.turns_left % 5) == 0:
                    app.printToGUI(
                        self.expiry_warning + str(self.turns_left) + " turns left. "
                    )


class AbstractClimbable(Thing):
    """Represents one end of a staircase or ladder.
	Creators should generally use a LadderConnector or StaircaseConnector (travel.py) rather than directly creating AbstractClimbable instances. """

    def __init__(self, name):
        """Sets essential properties for the AbstractClimbable instance """
        super().__init__(name)
        self.invItem = False


class Door(Thing):
    """Represents one side of a door. Always define with a twin, and set a direction. Can be open or closed.
	Creators should generally use DoorConnectors (travel.py) rather than defining Doors  directly. """

    def __init__(self, name):
        """Sets essential properties for the Door instance """
        super().__init__(name)
        self.invItem = False

        # TODO: create instance properties closed_desc and open_desc - possibly on Thing
        self.state_desc = "It is currently closed. "

    def makeOpen(self):
        self.is_open = True
        self.state_desc = "It is currently open. "
        self.desc = self.base_desc + self.state_desc
        self.xdesc = self.base_xdesc + self.state_desc
        if self.twin:
            if not self.twin.is_open:
                self.twin.makeOpen()
        if self.parent_obj:
            self.parent_obj.describeThing(self.parent_obj.base_desc)
            self.parent_obj.xdescribeThing(self.parent_obj.base_xdesc)

    def makeClosed(self):
        self.is_open = False
        self.state_desc = "It is currently closed. "
        self.desc = self.base_desc + self.state_desc
        self.xdesc = self.base_xdesc + self.state_desc
        if self.twin:
            if self.twin.is_open:
                self.twin.makeClosed()
        if self.parent_obj:
            self.parent_obj.describeThing(self.parent_obj.base_desc)
            self.parent_obj.xdescribeThing(self.parent_obj.base_xdesc)

    def describeThing(self, description):
        self.base_desc = description
        self.desc = description + self.state_desc
        if self.is_composite:
            if self.children_desc:
                self.desc = self.desc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc

    def xdescribeThing(self, description):
        self.base_xdesc = description
        self.xdesc = description + self.state_desc + self.lock_desc
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.xdesc = self.xdesc + item.desc

    def updateDesc(self):
        self.xdesc = self.base_xdesc + self.state_desc + self.lock_desc
        self.desc = self.base_desc + self.state_desc
        if self.is_composite:
            if self.children_desc:
                self.desc = self.desc + self.children_desc
                self.xdesc = self.xdesc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
                    self.xdesc = self.xdesc + item.desc


class Key(Thing):
    """Class for keys """

    def __init__(self, name="key"):
        """Sets essential properties for the Thing instance """
        super().__init__(name)


class Lock(Thing):
    """Lock is the class for lock items in the game  """

    def __init__(self, is_locked, key_obj, name="lock"):
        """Sets essential properties for the Lock instance """
        super().__init__(name)

        self.is_locked = is_locked
        self.key_obj = key_obj

        # TODO: extract strings into instance properties
        if self.is_locked:
            self.state_desc = " It is currently locked. "
        else:
            self.state_desc = "It is currently unlocked. "

    def makeUnlocked(self):
        self.is_locked = False
        self.state_desc = "It is currently unlocked. "
        self.xdesc = self.base_xdesc + self.state_desc
        if self.parent_obj:
            self.parent_obj.lock_desc = " It is unlocked. "
            self.parent_obj.updateDesc()
        if self.twin:
            if self.twin.is_locked:
                self.twin.makeUnlocked()

    def makeLocked(self):
        self.is_locked = True
        self.state_desc = "It is currently locked. "
        self.xdesc = self.base_xdesc + self.state_desc
        if self.parent_obj:
            self.parent_obj.lock_desc = " It is locked. "
            self.parent_obj.updateDesc()
        if self.twin:
            if not self.twin.is_locked:
                self.twin.makeLocked()

    def describeThing(self, description):
        self.base_desc = description
        self.desc = self.base_desc
        if self.is_composite:
            if self.children_desc:
                self.desc = self.desc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc

    def xdescribeThing(self, description):
        self.base_xdesc = description
        self.xdesc = self.base_xdesc + self.state_desc
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.xdesc = self.xdesc + item.desc


class Abstract(Thing):
    """Class for abstract game items with no location, such as ideas"""

    def __init__(self, name):
        super().__init__(name)

    def makeKnown(self, me):
        if not self.ix in me.knows_about:
            me.knows_about.append(self.ix)


class UnderSpace(Thing):
    """Things that can have other Things underneath """

    def __init__(self, name, me):
        """Set basic properties for the UnderSpace instance
		Takes argument name, a single noun (string)"""
        super().__init__(name)

        self._me = me
        self.size = 50
        self.contains_preposition = "under"
        self.contains_under = True
        self.contains_preposition_inverse = "out"

    def compositeBaseDesc(self):
        if self.is_composite:
            if self.children_desc:
                self.desc = self.base_desc + self.children_desc
            else:
                self.desc = self.base_desc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        else:
            self.desc = self.base_desc

    def compositeBasexDesc(self):
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                self.xdesc = self.base_xdesc
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        else:
            self.xdesc = self.base_xdesc

    def containsListUpdate(self, update_desc=True, update_xdesc=True):
        """Update description for addition/removal of items from the UnderSpace instance """
        from .actor import Player

        # desc = self.base_desc
        # xdesc = self.base_xdesc
        self.compositeBaseDesc()
        self.compositeBasexDesc()
        if not self.revealed:
            return False
        inlist = (
            " "
            + self.contains_preposition.capitalize()
            + " "
            + self.getArticle(True)
            + self.verbose_name
            + " is "
        )
        # iterate through contents, appending the verbose_name of each to onlist
        list_version = list(self.contains.keys())
        player_here = False
        for key in list_version:
            for item in self.contains[key]:
                if key in list_version:
                    if isinstance(item, Player):
                        list_version.remove(key)
                        player_here = True
                    elif item.parent_obj:
                        list_version.remove(key)
        for key in list_version:
            if len(self.contains[key]) > 1:
                inlist = (
                    inlist + str(len(things)) + " " + self.contains[key][0].verbose_name
                )
            else:
                inlist = (
                    inlist
                    + self.contains[key][0].getArticle()
                    + self.contains[key][0].verbose_name
                )
            if key is list_version[-1]:
                inlist = inlist + "."
            elif key is list_version[-2]:
                inlist = inlist + " and "
            else:
                inlist = inlist + ", "
            if key not in self._me.knows_about:
                self._me.knows_about.append(key)
        # remove the empty inlist in the case of no contents
        # TODO: consider rewriting this logic to avoid contructing an empty inlist, then deleting it
        if len(list_version) == 0:
            inlist = ""
        if player_here:
            if inlist != "":
                inlist = inlist + "<br>"
            inlist = (
                inlist + "You are in " + self.getArticle(True) + self.verbose_name + "."
            )
        # update descriptions
        if self.is_composite:
            if self.children_desc:
                self.desc = self.desc + self.children_desc
                self.xdesc = self.xdesc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
                    self.xdesc = self.xdesc + item.desc
            # self.desc = self.desc + inlist
            # self.xdesc = self.xdesc + inlist
        if update_desc and self.desc_reveal:
            self.desc = self.desc + inlist
        if update_xdesc and self.xdesc_reveal:
            self.xdesc = self.xdesc + inlist
        self.contains_desc = inlist
        return True

    def revealUnder(self):
        self.revealed = True
        self.containsListUpdate()
        for key in self.contains:
            next_loc = self.location
            for item in self.contains[key]:
                contentshidden = False
                if isinstance(item, Container):
                    if item.has_lid:
                        if item.is_open == False:
                            contentshidden = True
                while next_loc:
                    if not contentshidden:
                        nested = getNested(item)
                        if not isinstance(item, Actor):
                            for t in nested:
                                if t.ix in next_loc.sub_contains:
                                    if not t in next_loc.sub_contains[t.ix]:
                                        next_loc.sub_contains[t.ix].append(t)
                                else:
                                    next_loc.sub_contains[t.ix] = [t]
                    if item.ix in next_loc.sub_contains:
                        if not item in next_loc.sub_contains[item.ix]:
                            next_loc.sub_contains[item.ix].append(item)
                    else:
                        next_loc.sub_contains[item.ix] = [item]
                    next_loc = next_loc.location

    def moveContentsOut(self):
        contents = copy.copy(self.contains)
        out = ""
        list_version = list(contents.keys())
        counter = 0
        for key in contents:
            if len(contents[key]) == 1:
                out = (
                    out + contents[key][0].getArticle() + contents[key][0].verbose_name
                )
            else:
                n_things = str(len(contents[key]))
                out = out + n_things + contents[key][0].verbose_name
                counter = counter + 1
            if len(list_version) > 1:
                if key == list_version[-2]:
                    out = out + ", and "
                elif key != list_version[-1]:
                    out = out + ", "
            elif key != list_version[-1]:
                out = out + ", "
            for item in contents[key]:
                self.removeThing(item)
                self.location.addThing(item)
            counter = counter + 1
        if counter > 1:
            return [out, True]
        else:
            return [out, False]

    def addThing(self, item):
        """Add an item to contents, update descriptions
		Takes argument item, pointing to a Thing """
        item.location = self
        revealed = self.revealed
        if isinstance(item, Container):
            if item.lock_obj and (
                item.lock_obj.ix in self.contains
                or item.lock_obj.ix in self.sub_contains
            ):
                if not (
                    item.lock_obj in self.contains[item.lock_obj.ix]
                    or item.lock_obj in self.sub_contains[item.lock_obj.ix]
                ):
                    self.addThing(item.lock_obj)
            elif item.lock_obj:
                self.addThing(item.lock_obj)
        if item.is_composite:
            for item2 in item.children:
                if item2.ix in self.contains:
                    if not item2 in self.contains[item2.ix]:
                        self.addThing(item2)
                else:
                    self.addThing(item2)
        # nested items
        contentshidden = False
        if isinstance(item, Container):
            if item.has_lid:
                if item.is_open == False:
                    contentshidden = True
        nested = getNested(item)
        next_loc = self.location
        if revealed:
            while next_loc:
                if not isinstance(item, Actor):
                    for t in nested:
                        if t.ix in next_loc.sub_contains:
                            if not t in next_loc.sub_contains[t.ix]:
                                next_loc.sub_contains[t.ix].append(t)
                        else:
                            next_loc.sub_contains[t.ix] = [t]
                if item.ix in next_loc.sub_contains:
                    if not item in next_loc.sub_contains[item.ix]:
                        next_loc.sub_contains[item.ix].append(item)
                else:
                    next_loc.sub_contains[item.ix] = [item]
                next_loc = next_loc.location
        if not isinstance(item, Actor):
            for t in nested:
                if t.ix in self.sub_contains:
                    if not t in self.sub_contains[t.ix]:
                        self.sub_contains[t.ix].append(t)
                else:
                    self.sub_contains[t.ix] = [t]
        if item.ix in self.contains:
            self.contains[item.ix].append(item)
        else:
            self.contains[item.ix] = [item]
        self.revealed = revealed
        self.containsListUpdate()

    def removeThing(self, item, update_desc=True, update_xdesc=True):
        """Remove an item from contents, update decription """
        if isinstance(item, Container):
            if item.lock_obj:
                if item.lock_obj.ix in self.contains:
                    if item.lock_obj in self.contains[item.lock_obj.ix]:
                        self.removeThing(item.lock_obj)
                if item.lock_obj.ix in self.sub_contains:
                    if item.lock_obj in self.sub_contains[item.lock_obj.ix]:
                        self.removeThing(item.lock_obj)
        if item.is_composite:
            for item2 in item.children:
                if item2.ix in self.contains:
                    if item2 in self.contains[item2.ix]:
                        self.removeThing(item2)
                if item2.ix in self.sub_contains:
                    if item2 in self.sub_contains[item2.ix]:
                        self.removeThing(item2)
        nested = getNested(item)
        for t in nested:
            if t.ix in self.sub_contains:
                if t in self.sub_contains[t.ix]:
                    self.sub_contains[t.ix].remove(t)
                    if self.sub_contains[t.ix] == []:
                        del self.sub_contains[t.ix]
        next_loc = self.location
        while next_loc:
            if item.ix in next_loc.sub_contains:
                if item in next_loc.sub_contains[item.ix]:
                    next_loc.sub_contains[item.ix].remove(item)
                    if next_loc.sub_contains[item.ix] == []:
                        del next_loc.sub_contains[item.ix]
            for t in nested:
                if t.ix in next_loc.sub_contains:
                    if t in next_loc.sub_contains[t.ix]:
                        next_loc.sub_contains[t.ix].remove(t)
                        if next_loc.sub_contains[t.ix] == []:
                            del next_loc.sub_contains[t.ix]
            next_loc = next_loc.location
        rval = False
        if item.ix in self.contains:
            if item in self.contains[item.ix]:
                self.contains[item.ix].remove(item)
                if self.contains[item.ix] == []:
                    del self.contains[item.ix]
                rval = True
                item.location = False
                self.containsListUpdate(update_desc, update_xdesc)
        if item.ix in self.sub_contains:
            if item in self.sub_contains[item.ix]:
                self.sub_contains[item.ix].remove(item)
                if self.sub_contains[item.ix] == []:
                    del self.sub_contains[item.ix]
                rval = True
                item.location = False
                self.containsListUpdate(update_desc, update_xdesc)
        return rval

    def describeThing(self, description):
        self.base_desc = description
        self.desc = self.base_desc + self.state_desc
        if self.is_composite:
            if self.children_desc:
                self.desc = self.desc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.desc = self.desc + item.desc
        self.containsListUpdate()

    def xdescribeThing(self, description):
        self.base_xdesc = description
        self.xdesc = self.base_xdesc
        if self.is_composite:
            if self.children_desc:
                self.xdesc = self.xdesc + self.children_desc
            else:
                for item in self.children:
                    if item in self.child_UnderSpaces:
                        continue
                    self.xdesc = self.xdesc + item.desc
        self.containsListUpdate()

    def updateDesc(self):
        self.containsListUpdate()


def getNested(target):
    """Find revealed nested Things
	Takes argument target, pointing to a Thing
	Returns a list of Things
	Used by multiple verbs """
    # list to populate with found Things
    nested = []
    # iterate through top level contents
    if isinstance(target, Container):
        if target.has_lid:
            if target.is_open == False:
                return []
    for key in target.contains:
        for item in target.contains[key]:
            nested.append(item)
    for key in target.sub_contains:
        for item in target.sub_contains[key]:
            nested.append(item)
    return nested


class Transparent(Thing):
    """Transparent Things 
	Set the look_through_desc property to print the same string every time look through [instance as dobj] is used
	Replace default lookThrough method for more complicated behaviour """

    def __init__(self, name):
        """Sets essential properties for the Transparent instance """
        super().__init__(name)

    def lookThrough(self, me, app):
        """Called when the Transparent instance is dobj for verb look through
		Creators should overwrite for more complex behaviour """
        app.printToGUI(self.look_through_desc)


class Readable(Thing):
    """
    Readable Things 
    Set the read_desc property to print the same string every time 
    READ [instance as dobj] is used.

    Replace default readText method for more complicated behaviour
    """

    def __init__(self, name, text="There's nothing written here. "):
        """Sets essential properties for the Readable instance """
        super().__init__(name)

        self.read_desc = text  # the default description for the examine command

    def readText(self, me, app):
        """Called when the Transparent instance is dobj for verb look through
		Creators should overwrite for more complex behaviour """
        app.printToGUI(self.read_desc)


class Book(Readable):
    """Readable that can be opened """

    def __init__(self, name, text="There's nothing written here. "):
        """Sets essential properties for the Book instance """
        super().__init__(name, text)
        self.is_open = False

    def makeOpen(self):
        self.is_open = True
        self.desc = self.base_desc + "It is open. "
        self.xdesc = self.base_xdesc + "It is open. "

    def makeClosed(self):
        self.is_open = False
        self.desc = self.base_desc
        self.xdesc = self.base_xdesc


class Pressable(Thing):
    """
    Things that do something when pressed
    Game creators should redefine the pressThing method for the instance to trigger
    events when the PRESS/PUSH verb is used
    """

    def __init__(self, name):
        """Sets essential properties for the Pressable instance """
        super().__init__(name)

    def pressThing(self, me, app):
        """Game creators should redefine this method for their Pressable instances """
        app.printToGUI(self.capNameArticle(True) + " has been pressed. ")


class Liquid(Thing):
    """
    Can fill a container where holds_liquid is True, can be poured, and can
    optionally be drunk 

    Game creators should redefine the pressThing method for the instance to
    trigger events when the press/push verb is used
    """

    def __init__(self, name, liquid_type):
        """
        Sets essential properties for the Liquid instance 

        The liquid_type property should be a short description
        of what the liquid is, such as "water" or "motor oil"
        This will be used to determine what liquids can be merged and mixed
        Replace the mixWith property to allow mixing of Liquids
        """
        super().__init__(name)

        self.can_drink = True
        self.can_pour_out = True
        self.can_fill_from = True
        self.infinite_well = False
        self.liquid_for_transfer = self
        self.liquid_type = liquid_type
        self.cannot_fill_from_msg = (
            "You are unable to collect any of the spilled " + name + ". "
        )
        self.cannot_pour_out_msg = "You shouldn't dump that out. "
        self.cannot_drink_msg = "You shouldn't drink that. "

        self.is_numberless = True

        self.base_desc = "There is " + self.getArticle() + self.verbose_name + " here. "
        self.base_xdesc = self.base_desc
        self.desc = self.base_desc
        self.xdesc = self.base_xdesc

    def getContainer(self):
        """Redirect to the Container rather than the Liquid for certain verbs (i.e. take) """
        if isinstance(self.location, Container):
            return self.location
        else:
            return None

    def dumpLiquid(self):
        """Defines what happens when the Liquid is dumped out"""
        loc = self.getOutermostLocation()
        if not isinstance(self.location, Container) or not self.can_pour_out:
            return False
        self.location.removeThing(self)
        loc.addThing(self)
        self.describeThing(
            self.capNameArticle() + " has been spilled on the ground here. "
        )
        self.invItem = False
        self.can_fill_from = False
        return True

    def fillVessel(self, vessel):
        """Used for verbs fill from and pour into """
        vessel_liquid = vessel.containsLiquid()
        vessel_left = vessel.liquidRoomLeft()
        if vessel_liquid:
            if vessel_left == 0:
                return False
            if not self.can_fill_from:
                return False
            elif vessel_liquid.liquid_type != self.liquid_type:
                return self.mixWith(vessel_liquid)
            else:
                return False
        else:
            if self.infinite_well:
                vessel_liquid = self.liquid_for_transfer.copyThing()
                # vessel_liquid.infinite_well = False
                # vessel_liquid.size = vessel.size
                vessel.addThing(vessel_liquid)
                return True
            else:
                self.location.removeThing(self)
                vessel.addThing(self.liquid_for_transfer)
                return True

    def mixWith(self, me, app, base_liquid, mix_in):
        """Replace to allow mixing of specific Liquids
		Return True when a mixture is allowed, False otherwise """
        return False

    def drinkLiquid(self, me, app):
        """Replace for custom effects for drinking the Liquid """
        self.location.removeThing(self)
        return True

    def getArticle(self, definite=False):
        """Gets the correct article for a Thing
		Takes argument definite (defaults to False), which specifies whether the article is definite
		Returns a string """
        if not self.hasArticle:
            return ""
        elif definite or self.isDefinite:
            return "the "
        elif self.is_numberless:
            return ""
        else:
            if self.verbose_name[0] in ["a", "e", "i", "o", "u"]:
                return "an "
            else:
                return "a "


# hacky solution for reflexive pronouns (himself/herself/itself)
reflexive = Abstract("itself")
reflexive.addSynonym("himself")
reflexive.addSynonym("herself")
reflexive.addSynonym("themself")
reflexive.addSynonym("themselves")