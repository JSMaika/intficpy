import unittest

from .helpers import IFPTestCase

from intficpy.thing_base import Thing
from intficpy.things import Surface, UnderSpace
from intficpy.vocab import nounDict
from intficpy.actor import Actor, SpecialTopic
from intficpy.verb import (
    Verb,
    getVerb,
    lookVerb,
    setOnVerb,
    leadDirVerb,
    jumpOverVerb,
    giveVerb,
    examineVerb,
    getAllVerb,
)
from intficpy.exceptions import ObjectMatchError


class TestParser(IFPTestCase):
    def test_verb_with_no_objects(self):
        self.game.turnMain("look")

        self.assertIs(self.game.parser.previous_command.verb, lookVerb)
        self.assertIsNone(self.game.parser.previous_command.dobj.target)
        self.assertIsNone(self.game.parser.previous_command.iobj.target)

    def test_verb_with_dobj_only(self):
        dobj = Thing(self._get_unique_noun())
        self.start_room.addThing(dobj)

        self.game.turnMain(f"get {dobj.name}")

        self.assertIs(self.game.parser.previous_command.verb, getVerb)
        self.assertIs(self.game.parser.previous_command.dobj.target, dobj)
        self.assertIsNone(self.game.parser.previous_command.iobj.target)

    def test_gets_correct_verb_with_dobj_and_direction_iobj(self):
        dobj = Actor(self._get_unique_noun())
        self.start_room.addThing(dobj)
        iobj = "east"
        self.start_room.east = self.start_room

        self.game.turnMain(f"lead {dobj.name} {iobj}")

        self.assertIs(self.game.parser.previous_command.verb, leadDirVerb)
        self.assertIs(self.game.parser.previous_command.dobj.target, dobj)
        self.assertEqual(self.game.parser.previous_command.iobj.target, iobj)

    def test_gets_correct_verb_with_preposition_dobj_only(self):
        dobj = Thing(self._get_unique_noun())
        self.start_room.addThing(dobj)

        self.game.turnMain(f"jump over {dobj.name}")

        self.assertIs(self.game.parser.previous_command.verb, jumpOverVerb)
        self.assertIs(self.game.parser.previous_command.dobj.target, dobj)
        self.assertIsNone(self.game.parser.previous_command.iobj.target)

    def test_gets_correct_verb_with_preposition_dobj_and_iobj(self):
        dobj = Thing(self._get_unique_noun())
        self.start_room.addThing(dobj)
        iobj = Surface(self._get_unique_noun())
        self.start_room.addThing(iobj)

        self.game.turnMain(f"set {dobj.name} on {iobj.name}")

        self.assertIs(self.game.parser.previous_command.verb, setOnVerb)
        self.assertIs(self.game.parser.previous_command.dobj.target, dobj)
        self.assertIs(self.game.parser.previous_command.iobj.target, iobj)


class TestGetGrammarObj(IFPTestCase):
    def test_gets_correct_objects_with_adjacent_dobj_iobj(self):
        dobj_item = Actor(self._get_unique_noun())
        self.start_room.addThing(dobj_item)
        iobj_item = Thing(self._get_unique_noun())
        self.start_room.addThing(iobj_item)

        self.game.turnMain(f"give {dobj_item.name} {iobj_item.name}")

        self.assertEqual(self.game.parser.previous_command.dobj.target, dobj_item)
        self.assertEqual(self.game.parser.previous_command.iobj.target, iobj_item)


class TestAdjacentStrObj(IFPTestCase):
    def setUp(self):
        super().setUp()

        self.strangeVerb = Verb("strange")
        self.strangeVerb.syntax = [["strange", "<iobj>", "<dobj>"]]
        self.strangeVerb.hasDobj = True
        self.strangeVerb.hasIobj = True
        self.strangeVerb.hasStrIobj = True
        self.strangeVerb.iscope = "text"
        self.strangeVerb.dscope = "near"

        def strangeVerbFunc(game, dobj, iobj):
            game.addTextToEvent("turn", "You do strange things")
            return True

        self.strangeVerb.verbFunc = strangeVerbFunc

    def test_thing_follows_string_adjacent_string_object(self):
        thing = Thing("thing")
        thing.setAdjectives(["good"])
        self.start_room.addThing(thing)

        self.game.turnMain("strange purple good thing")

        self.assertIs(
            self.game.parser.previous_command.verb,
            self.strangeVerb,
            "Unexpected verb from command with adjacent string objects where thing "
            "follows string",
        )
        self.assertIs(
            self.game.parser.previous_command.dobj.target,
            thing,
            "Unexpected dobj from command with adjacent string objects where thing "
            "follows string",
        )


class TestGetThing(IFPTestCase):
    def test_get_thing(self):
        noun = self._get_unique_noun()
        self.assertNotIn(
            noun,
            nounDict,
            f"This test needs the value of noun ({noun}) to be such that it does not "
            "initially exist in nounDict",
        )
        item1 = Thing(noun)
        self.start_room.addThing(item1)
        self.assertTrue(
            noun in nounDict, "Name was not added to nounDict after Thing creation"
        )

        self.game.turnMain(f"examine {noun}")
        self.assertIs(
            self.game.parser.previous_command.dobj.target,
            item1,
            "Failed to match item from unambiguous noun",
        )

        item2 = Thing(noun)
        self.start_room.addThing(item2)
        self.assertEqual(len(nounDict[noun]), 2)

        adj1 = "unique"
        adj2 = "special"
        self.assertNotEqual(
            adj1, adj2, "This test requires that adj1 and adj2 are not equal"
        )

        item1.setAdjectives([adj1])
        item2.setAdjectives([adj2])

        self.game.turnMain(f"examine {noun}")

        self.assertEqual(self.game.parser.previous_command.dobj.tokens, [noun])

        self.game.turnMain(f"examine {adj1} {noun}")
        self.assertIs(
            self.game.parser.previous_command.dobj.target,
            item1,
            "Noun adjective array should have been unambiguous, but failed to match "
            "Thing",
        )


class TestParserError(IFPTestCase):
    def test_verb_not_understood(self):
        self.game.turnMain("thisverbwillnevereverbedefined")

        msg = self.app.print_stack.pop()
        expected = "I don't understand the verb:"

        self.assertIn(expected, msg, "Unexpected response to unrecognized verb.")

    def test_suggestion_not_understood(self):
        topic = SpecialTopic(
            "tell sarah to grow a beard", "You tell Sarah to grow a beard."
        )

        self.game.parser.previous_command.specialTopics[
            "tell sarah to grow a beard"
        ] = topic

        self.game.turnMain("thisverbwillnevereverbedefined")

        msg = self.app.print_stack.pop()
        expected = "is not enough information to match a suggestion"

        self.assertIn(expected, msg, "Unexpected response to unrecognized suggestion.")

    def test_noun_not_understood(self):
        self.game.turnMain("take thisnounwillnevereverbedefined")

        msg = self.app.print_stack.pop()
        expected = "I don't see any"

        self.assertIn(expected, msg, "Unexpected response to unrecognized noun.")

    def test_verb_by_objects_unrecognized_noun(self):
        self.game.turnMain("lead sarah")

        msg = self.app.print_stack.pop()
        expected = "I understood as far as"

        self.assertIn(
            expected,
            msg,
            "Unexpected response attempting to disambiguate verb with unrecognized "
            "noun.",
        )

    def test_verb_by_objects_no_near_matches_unrecognized_noun(self):
        sarah1 = Actor("teacher")
        sarah1.setAdjectives(["good"])
        self.start_room.addThing(sarah1)

        sarah2 = Actor("teacher")
        sarah2.setAdjectives(["bad"])
        self.start_room.addThing(sarah2)

        self.game.turnMain("hi teacher")
        self.assertTrue(self.game.parser.previous_command.ambiguous)

        self.game.turnMain("set green sarah")

        msg = self.app.print_stack.pop()
        expected = "I understood as far as"

        self.assertIn(
            expected,
            msg,
            "Unexpected response attempting to disambiguate verb with unrecognized "
            "noun.",
        )


class TestCompositeObjectRedirection(IFPTestCase):
    def test_composite_object_redirection(self):
        bench = Surface("bench")
        self.start_room.addThing(bench)
        underbench = UnderSpace("space")
        bench.addComposite(underbench)

        widget = Thing("widget")
        underbench.addThing(widget)

        self.game.turnMain("look under bench")
        msg = self.app.print_stack.pop()

        self.assertIn(
            widget.verbose_name,
            msg,
            "Unexpected response attempting to use a component redirection",
        )


class TestDisambig(IFPTestCase):
    def test_disambiguate_with_directional_adjective(self):
        east_pillar = Thing("pillar")
        east_pillar.setAdjectives(["east"])
        west_pillar = Thing("pillar")
        west_pillar.setAdjectives(["west"])

        self.start_room.addThing(east_pillar)
        self.start_room.addThing(west_pillar)

        self.game.turnMain("x pillar")

        self.assertTrue(self.game.parser.previous_command.ambiguous)

        self.game.turnMain("east")

        self.assertIs(
            self.game.parser.previous_command.dobj.target,
            east_pillar,
            "Unexpected direct object after attempting to disambiguate with direction "
            "adjective",
        )

    def test_disambiguate_with_index(self):
        east_pillar = Thing("pillar")
        east_pillar.setAdjectives(["east"])
        west_pillar = Thing("pillar")
        west_pillar.setAdjectives(["west"])

        self.start_room.addThing(east_pillar)
        self.start_room.addThing(west_pillar)

        self.game.turnMain("x pillar")

        self.assertTrue(self.game.parser.previous_command.ambiguous)

        self.game.turnMain("1")

        self.assertIn(
            self.game.parser.previous_command.dobj.target,
            [east_pillar, west_pillar],
            "Unexpected direct object after attempting to disambiguate with index",
        )


class TestPrepositions(IFPTestCase):
    def test_prepositional_adjectives(self):
        up_ladder = Thing(self._get_unique_noun())
        up_ladder.setAdjectives(["high", "up"])

        self.start_room.addThing(up_ladder)

        self.game.turnMain(f"x up high {up_ladder.name}")

        self.assertIs(
            self.game.parser.previous_command.verb,
            examineVerb,
            "Unexpected verb after using a preposition as an adjective",
        )

        self.assertIs(
            self.game.parser.previous_command.dobj.target,
            up_ladder,
            "Unexpected dobj after using a preposition as an adjective",
        )

    def test_verb_rejected_if_preposition_not_accounted_for(self):
        up_ladder = Thing(self._get_unique_noun())

        self.start_room.addThing(up_ladder)

        self.game.turnMain(f"x up big {up_ladder.name}")

        self.assertIsNot(
            self.game.parser.previous_command.verb,
            examineVerb,
            "Examine verb does not have preposition `up`. Should not have matched.",
        )

    def test_preposition_directional_verb(self):
        girl = Thing("girl")

        self.start_room.addThing(girl)

        self.game.turnMain(f"lead girl up")

        self.assertIs(
            self.game.parser.previous_command.verb,
            leadDirVerb,
            "Unexpected verb after using a direction that doubles as a preposition (up) "
            "for a directional verb",
        )


class TestKeywords(IFPTestCase):
    def test_keyword_adjectives(self):
        everything_box = Thing(self._get_unique_noun())
        everything_box.setAdjectives(["good", "everything"])

        self.start_room.addThing(everything_box)

        self.game.turnMain(f"x everything good {everything_box.name}")

        self.assertIs(
            self.game.parser.previous_command.verb,
            examineVerb,
            "Unexpected verb after using an english keyword as an adjective",
        )

        self.assertIs(
            self.game.parser.previous_command.dobj.target,
            everything_box,
            "Unexpected dobj after using an english keyword as an adjective",
        )

    def test_verb_rejected_if_keyword_not_accounted_for(self):
        everything_box = Thing(self._get_unique_noun())

        self.start_room.addThing(everything_box)

        self.game.turnMain(f"x everything good {everything_box.name}")

        self.assertIsNot(
            self.game.parser.previous_command.verb,
            examineVerb,
            "Examine verb does not have keyword `everything`. Should not have matched.",
        )

    def test_verb_with_keyword(self):
        self.game.turnMain("take all")

        self.assertIs(
            self.game.parser.previous_command.verb,
            getAllVerb,
            "Tried to call a verb with an english keyword.",
        )


class TestSuggestions(IFPTestCase):
    def test_accept_suggestion(self):
        girl = Actor("girl")
        TOPIC_SUGGESTION = "ask what her name is"
        TOPIC_TEXT = '"It\'s Karen," says the girl.'
        topic = SpecialTopic(TOPIC_SUGGESTION, TOPIC_TEXT)
        girl.addSpecialTopic(topic)
        self.start_room.addThing(girl)

        self.game.turnMain("talk to girl")
        self.assertTrue(self.game.parser.previous_command.specialTopics)

        self.game.turnMain(TOPIC_SUGGESTION)

        msg = self.app.print_stack.pop(-2)

        self.assertEqual(
            msg, TOPIC_TEXT, "Expected topic text to print after accepting suggestion"
        )


if __name__ == "__main__":
    unittest.main()
