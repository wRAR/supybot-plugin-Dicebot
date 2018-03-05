###
# Copyright (c) 2018, Anatoly Popov
# Copyright (c) 2018, Andrey Rahmatullin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import random
import pytest
from collections import defaultdict

class RollResult:
    def __init__(self, result, lash_count=0, joie_de_vivre_target=0, explode_level=0):
        self.result = result
        self.explode_level = explode_level
        if result < lash_count:
            self.value = 0
        elif result <= joie_de_vivre_target:
            self.value = 10
        else:
            self.value = result

    def __str__(self):
        if self.result == self.value:
            return "%d%s" % (self.result, "x" * self.explode_level)
        else:
            return "%d%s [%d]" % (self.value, "x" * self.explode_level, self.result)

class Raise:
    def __init__(self, raise_count=0, rolls=[]):
        self.rolls = list(map(lambda x: x if isinstance(x, RollResult) else RollResult(x), rolls))
        self.raise_count = raise_count

    def __str__(self):
        if self.raise_count == 0:
            return "(%s)" % (" + ".join(map(str, self.rolls)))
        else:
            return "%s(%s)" % ("*" * self.raise_count, " + ".join(map(str, self.rolls)))

class RaiseRollResult:
    def __init__(self, raises=[], unused=[], discarded=None):
        self.raises = raises
        self.unused = unused
        self.discarded = discarded

    def __str__(self):
        total_raises = sum(x.raise_count for x in self.raises)
        result = "0 raises" if total_raises == 0 else "%d %s: %s" % (
            total_raises,
            "raises" if total_raises != 1 else "raise",
            ", ".join(map(str, self.raises))
        )

        if self.unused:
            result = "%s, unused: %s" % (
                result,
                ", ".join(map(str, self.unused))
            )

        if self.discarded:
            result = "%s, discarded: %s" % (
                result,
                ", ".join(map(str, self.discarded))
            )

        return result

class RaiseAggregator:
    def __init__(self, raise_target, raises_per_target, lash_count, joie_de_vivre_target, rolls):
        self.raise_target = raise_target
        self.raises_per_target = raises_per_target
        self.ten_is_still_raise = self.raise_target == 10 or self.raises_per_target != 1
        self.exhausted = False

        self.rolled_dices = defaultdict(list)
        self.dices = defaultdict(list)
        self.max_roll = 0
        for x in rolls:
            self.rolled_dices[x.value].append(x)
            if x.value > self.max_roll:
                self.max_roll = x.value

    def get_dice(self, max):
        for x in range(max, 0, -1):
            if len(self.dices[x]) > 0:
                return self.dices[x].pop()

        for x in range(max + 1, self.max_roll+ 1):
            if len(self.dices[x]) > 0:
                return self.dices[x].pop()

        return None

    def __iter__(self):
        self.dices = defaultdict(list)
        for value in self.rolled_dices:
            for roll in self.rolled_dices[value]:
                self.dices[value].append(roll)
        self.exhausted = False
        return self

    def __next__(self):
        if self.exhausted:
            raise StopIteration

        raise_candidate = []
        raise_count = self.raises_per_target
        while True:
            raise_sum = sum(x.value for x in raise_candidate)
            next_dice = self.get_dice(self.raise_target - raise_sum)
            if next_dice is not None:
                raise_candidate.append(next_dice)
                if raise_sum + next_dice.value >= self.raise_target:
                    break
            else:
                if self.ten_is_still_raise and raise_sum >= 10:
                    raise_count = 1
                    break

                self.exhausted = True
                for x in raise_candidate:
                    self.dices[x.value].append(x)
                raise StopIteration

        return Raise(raise_count, raise_candidate)

class SevenSea2EdRaiseRoller:
    """
    Raise roller for 7sea, 2ed. Spec: https://redd.it/80l7jm
    """

    def __init__(self, roller, raise_target=10, raises_per_target=1, explode=False, lash_count=0, skill_rank=0, joie_de_vivre=False):
        self.roller = roller
        self.explode = skill_rank >= 5 or explode
        self.lash_count = lash_count
        self.joie_de_vivre_target = skill_rank if joie_de_vivre else 0
        self.reroll_one_dice = skill_rank >= 3
        default_roll = raise_target == 10 and raises_per_target == 1
        self.aggregator_template = lambda x: RaiseAggregator(
            15 if skill_rank >= 4 and default_roll else raise_target,
            2 if skill_rank >= 4 and default_roll else raises_per_target,
            lash_count,
            skill_rank if joie_de_vivre else 0,
            x
        )

    def roll_and_count(self, dice_count):
        """
        Assemble raises, according to spec
        """
        rolls = self.roll(dice_count)
        if not self.reroll_one_dice:
            discarded_dice = None
        else:
            reroll = self.roll(1)
            min_value_dice = min(rolls, key=lambda x: x.value)
            if min_value_dice.value < sum(x.value for x in reroll):
                rolls.remove(min_value_dice)
                rolls += reroll
                discarded_dice = [min_value_dice]
            else:
                discarded_dice = reroll

        aggregator = self.aggregator_template(rolls)
        raises = list(aggregator)
        unused = []
        for value in aggregator.dices:
            for dice in aggregator.dices[value]:
                unused.append(dice)

        return RaiseRollResult(raises, sorted(unused, key=lambda x: x.value, reverse=True), discarded_dice)

    def roll(self, dice_count, explode_level=0):
        if dice_count == 0:
            return []

        rolls = [RollResult(x, self.lash_count, self.joie_de_vivre_target, explode_level) for x in self.roller(dice_count)]

        return rolls + self.roll(len([x for x in rolls if x.result == 10]), explode_level + 1) if self.explode else rolls
