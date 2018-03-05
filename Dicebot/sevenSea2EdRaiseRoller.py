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
    def __init__(self, result, lash_count=0, joie_de_vivre_target=0):
        self.result = result
        if result < lash_count:
            self.value = 0
        elif result <= joie_de_vivre_target:
            self.value = 10
        else:
            self.value = result

    def __str__(self):
        return "%d" % (self.result) if self.result == self.value else "%d [%d]" % (self.value, self.result)

class Raise:
    def __init__(self, raise_count=0, rolls=[]):
        self.rolls = list(map(lambda x: x if isinstance(x, RollResult) else RollResult(x), rolls))
        self.raise_count = raise_count

    @property
    def Sum(self):
        return sum(map(lambda x: x.value, self.rolls))

    def __str__(self):
        if self.raise_count == 0:
            return "(%s)" % (" + ".join(map(str, self.rolls)))
        else:
            return "%s(%s)" % ("*" * self.raise_count, " + ".join(map(str, self.rolls)))

class RaiseRollResult:
    def __init__(self, raises=[], unused=[]):
        self.raises = raises
        self.unused = unused

    def __str__(self):
        total_raises = sum(x.raise_count for x in self.raises)
        result = "0 raises" if total_raises == 0 else "%d %s: %s" % (
            total_raises,
            "raises" if total_raises != 1 else "raise",
            ", ".join(map(str, self.raises))
        )

        if not self.unused:
            return result

        return "%s, unused: %s" % (
            result,
            ", ".join(map(str, self.unused))
        )

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
            result = RollResult(x, lash_count, joie_de_vivre_target)
            self.dices[result.value].append(result)
            self.rolled_dices[result.value].append(result)
            if result.value > self.max_roll:
                self.max_roll = result.value

    def get_dice(self, max):
        for x in range(max, 0, -1):
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
        self.aggregator_template = lambda x: RaiseAggregator(
            15 if skill_rank >= 4 else raise_target,
            2 if skill_rank >= 4 else raises_per_target,
            lash_count,
            skill_rank if joie_de_vivre else 0,
            x
        )

    def roll_and_count(self, dice_count):
        """
        Assemble raises, according to spec
        """
        aggregator = self.aggregator_template(self.roll(dice_count))
        raises = list(sorted(aggregator, key=lambda x: x.Sum, reverse=True))
        unused = []
        for value in aggregator.dices:
            for dice in aggregator.dices[value]:
                unused.append(dice)

        return RaiseRollResult(raises, sorted(unused, key=lambda x: x.value, reverse=True))

    def roll(self, dice_count):
        if dice_count == 0:
            return []

        rolls = self.roller(dice_count)

        return rolls + self.roll(len([x for x in rolls if x == 10])) if self.explode else rolls
