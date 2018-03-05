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
        self.rolls = map(lambda x: x if isinstance(x, RollResult) else RollResult(x), rolls)
        self.raise_count = raise_count

    @property
    def Sum(self):
        return sum(map(lambda x: x.value, self.rolls))

    def __str__(self):
        if self.raise_count == 0:
            return "(%s)" % (" + ".join(map(str, self.rolls)))
        else:
            return "%s (%s)" % ("*" * self.raise_count, " + ".join(map(str, self.rolls)))

class Result:
    def __init__(self, raises=[], unused=[]):
        self.raises = raises
        self.unused = unused

    def __str__(self):
        total_raises = sum(map(lambda x: x.raise_count, self.raises))
        result = "%d %s: %s" % (
            total_raises,
            "raises" if total_raises != 1 else "raise",
            "; ".join(map(str, self.raises))
        )

        if not self.unused:
            return result

        return "%s, unused: %s" %(
            result,
            map(str, self.unused)
        )

class SevenSea2EdRaiseAssembler:
    """
    Raise assembler for 7sea, 2ed. Spec: https://redd.it/80l7jm
    """

    def __init__(self, roller, raise_target=10, raises_per_target=1, explode=False, lash_count=0, skill_rank=0, joie_de_vivre=False):
        self.roller = roller
        self.raise_target = raise_target
        self.raises_per_target = raises_per_target
        self.explode = explode
        self.lash_count = lash_count
        self.skill_rank = skill_rank
        self.joie_de_vivre_target = self.skill_rank if joie_de_vivre else 0

        if skill_rank >= 4:
            self.raise_target = 15
            self.raises_per_target = 2
        if skill_rank >= 5:
            self.explode = True

        self.ten_is_still_raise = self.raise_target == 10 or self.raises_per_target != 1
        self.breaker = 0

    def roll_and_count(self, dice_count):
        """
        Assemble raises, according to spec
        """
        dices = self.roll(dice_count)
        return Result()

    def roll(self, dice_count):
        if dice_count == 0:
            return []

        if self.breaker == 10:
            return []

        rolls = [RollResult(x, self.lash_count, self.joie_de_vivre_target) for x in self.roller(dice_count)]
        self.breaker += 1
        return rolls + self.roll(len([x for x in rolls if x.result == 10])) if self.explode else rolls

