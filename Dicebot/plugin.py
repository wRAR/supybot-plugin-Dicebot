###
# Copyright (c) 2007-2008, Andrey Rahmatullin
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

from .deck import Deck

import re
import random

from supybot.commands import wrap
from supybot.utils.str import format
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks

class Dicebot(callbacks.Plugin):
    """This plugin supports rolling the dice using !roll 4d20+3 as well as
    automatically rolling such combinations it sees in the channel (if
    autoRoll option is enabled for that channel) or query (if
    autoRollInPrivate option is enabled).
    """

    rollReStandard = re.compile(r'\b(?P<dice>\d*)d(?P<sides>\d+)(?P<mod>[+-]\d+)?\b')
    rollReMultiple = re.compile(r'\b(?P<rolls>\d+)#(?P<dice>\d*)d(?P<sides>\d+)(?P<mod>[+-]\d+)?\b')
    rollReSR       = re.compile(r'\b(?P<rolls>\d+)#sd\b')
    rollReSRX      = re.compile(r'\b(?P<rolls>\d+)#sdx\b')
    rollRe7Sea     = re.compile(r'(?P<prefix>-|\+)?(?P<rolls>\d+)(?P<k>k{1,2})(?P<keep>\d+)(?P<mod>[+-]\d+)?')

    MAX_DICE = 1000
    MIN_SIDES = 2
    MAX_SIDES = 100
    MAX_ROLLS = 30

    def __init__(self, irc):
        super(Dicebot, self).__init__(irc)
        self.deck = Deck()

    def _roll(self, dice, sides, mod=0):
        res = int(mod)
        for i in xrange(dice):
            res += random.randrange(1, sides+1)
        return res

    def _rollMultiple(self, dice, sides, rolls=1, mod=0):
        return [self._roll(dice, sides, mod) for i in xrange(rolls)]

    def _formatMod(self, mod):
        if mod != 0:
            return '%+d' % mod
        else:
            return ''

    def _process(self, irc, text):
        checklist = [
                (self.rollReMultiple, self._parseMultipleRoll),
                (self.rollReStandard, self._parseStandardRoll),
                (self.rollReSR, self._parseShadowrunRoll),
                (self.rollReSRX, self._parseShadowrunXRoll),
                (self.rollRe7Sea, self._parse7SeaRoll),
                ]
        results = [ ]
        for word in text.split():
            for expr, parser in checklist:
                m = expr.search(word)
                if m:
                    r = parser(m)
                    if r:
                        results.append(r)
                        break
        if results:
            irc.reply('; '.join(results))

    def _parseStandardRoll(self, m):
        dice = int(m.group('dice') or 1)
        sides = int(m.group('sides'))
        mod = int(m.group('mod') or 0)
        if dice > self.MAX_DICE or sides > self.MAX_SIDES or sides < self.MIN_SIDES:
            return
        res = self._roll(dice, sides, mod)
        return '[%dd%d%s] %d' % (dice, sides, self._formatMod(mod), res)

    def _parseMultipleRoll(self, m):
        rolls = int(m.group('rolls') or 0)
        dice = int(m.group('dice') or 1)
        sides = int(m.group('sides'))
        mod = int(m.group('mod') or 0)
        if dice > self.MAX_DICE or sides > self.MAX_SIDES or sides < self.MIN_SIDES or rolls < 1 or rolls > self.MAX_ROLLS:
            return
        L = self._rollMultiple(dice, sides, rolls, mod)
        return '[%dd%d%s] %s' % (dice, sides, self._formatMod(mod),
                                 ', '.join([str(i) for i in L]))

    def _parseShadowrunRoll(self, m):
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return
        L = self._rollMultiple(1, 6, rolls)
        self.log.debug(format("%L", [str(i) for i in L]))
        return self._processSRResults(L, rolls)

    def _parseShadowrunXRoll(self, m):
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return
        L = self._rollMultiple(1, 6, rolls)
        self.log.debug(format("%L", [str(i) for i in L]))
        reroll = L.count(6)
        while reroll:
            rerolled = self._rollMultiple(1, 6, reroll)
            self.log.debug(format("%L", [str(i) for i in rerolled]))
            L.extend([r for r in rerolled if r >= 5])
            reroll = rerolled.count(6)
        return self._processSRResults(L, rolls, True)

    def _processSRResults(self, results, pool, isExploding=False):
        hits = results.count(6) + results.count(5)
        ones = results.count(1)
        isHit = hits > 0
        isGlitch = ones >= (pool + 1) / 2
        explStr = ', exploding' if isExploding else ''
        if isHit:
            hitsStr = 'hits' if hits > 1 else 'hit'
            glitchStr = ', glitch' if isGlitch else ''
            return '(pool %d%s) %d %s%s' % (pool, explStr, hits, hitsStr, glitchStr)
        if isGlitch:
            return '(pool %d%s) critical glitch!' % (pool, explStr)
        return '(pool %d%s) 0 hits' % (pool, explStr)

    def _parse7SeaRoll(self, m):
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return
        keep = int(m.group('keep'))
        mod = int(m.group('mod') or 0)
        prefix = m.group('prefix')
        k = m.group('k')
        explode = prefix != '-'
        unkept = (prefix == '+' or k == 'kk') and keep < rolls
        if keep < 1 or keep > self.MAX_ROLLS:
            return
        if keep > rolls:
            keep = rolls
        L = self._rollMultiple(1, 10, rolls)
        if explode:
            for i in xrange(len(L)):
                if L[i] == 10:
                    while True:
                        rerolled = self._roll(1, 10)
                        L[i] += rerolled
                        if rerolled < 10:
                            break
        self.log.debug(format("%L", [str(i) for i in L]))
        L.sort(reverse=True)
        keptDice = L[:keep]
        unkeptDice = L[keep:]
        explodeStr = ', not exploding' if not explode else ''
        unkeptStr = ' | %s' % ', '.join([str(i) for i in unkeptDice]) if unkept else ''

        return '[%dk%d%s%s] (%d) %s%s' % (rolls, keep, self._formatMod(mod),
                                          explodeStr, sum(keptDice) + mod,
                                          ', '.join([str(i) for i in keptDice]),
                                          unkeptStr)

    def _autoRollEnabled(self, irc, channel):
        return ((irc.isChannel(channel) and
                self.registryValue('autoRoll', channel)) or
                (not irc.isChannel(channel) and
                self.registryValue('autoRollInPrivate')))

    def roll(self, irc, msg, args, text):
        """<dice>d<sides>[<modifier>]

        Rolls a die with <sides> number of sides <dice> times, summarizes the
        results and adds optional modifier <modifier>
        For example, 2d6 will roll 2 six-sided dice; 10d10-3 will roll 10
        ten-sided dice and subtract 3 from the total result.
        """
        if self._autoRollEnabled(irc, msg.args[0]):
            return
        self._process(irc, text)
    roll = wrap(roll, ['somethingWithoutSpaces'])

    def shuffle(self, irc, msg, args):
        """takes no arguments

        Restores and shuffles the deck."""
        self.deck.shuffle()
        irc.reply('shuffled')
    shuffle = wrap(shuffle)

    def draw(self, irc, msg, args):
        """takes no arguments

        Draws a card from the deck and shows it."""
        card = self.deck.next()
        irc.reply(card)
    draw = wrap(draw)
    deal = draw

    def doPrivmsg(self, irc, msg):
        if not self._autoRollEnabled(irc, msg.args[0]):
            return
        if ircmsgs.isAction(msg):
            text = ircmsgs.unAction(msg)
        else:
            text = msg.args[1]
        self._process(irc, text)

Class = Dicebot


# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
