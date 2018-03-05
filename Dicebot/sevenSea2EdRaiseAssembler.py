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

class SevenSea2EdRaiseAssembler:
    """
    Raise assembler for 7sea, 2ed. Spec: https://redd.it/80l7jm
    """

    def __init__(self, roller):
        self.roller = roller
        self.raise_target = 10
        self.raises_per_target = 1
        self.explode = False
        self.discard_target = 0
        self.joie_de_vivre = False

    def roll(self, dice_count):
        self.dice_count = dice_count
        return self

    def with_skill(self, rank):
        self.skill_rank = rank
        if rank >= 4:
            self.raise_target = 15
            self.raises_per_target = 2
        if rank >= 5:
            self.explode = True
        return self

    def with_lashes(self, count):
        self.discard_target = count
        return self

    def with_joie_de_vivre(self):
        self.joie_de_vivre = True
        return self

    def with_explode(self):
        self.explode = True
        return self

    def assemble(self):
        """
        Assemble raises, according to spec
        """

