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

import re
import random

import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

from supybot.utils.iter import all

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

    MAX_DICE = 1000
    MIN_SIDES = 2
    MAX_SIDES = 100
    MAX_ROLLS = 30

    def _roll(self, dice, sides, mod=0):
        res = int(mod)
        for i in xrange(dice):
            res += random.randrange(1, sides+1)
        return res

    def _formatMod(self, mod):
        if mod < 0:
            return str(mod)
        elif mod > 0:
            return '+' + str(mod)
        else:
            return ''

    def _process(self, irc, text):
        checklist = [
                (self.rollReMultiple, self._parseMultipleRoll),
                (self.rollReStandard, self._parseStandardRoll),
                (self.rollReSR, self._parseShadowrunRoll),
                (self.rollReSRX, self._parseShadowrunXRoll),
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
        L = [str(self._roll(dice, sides, mod)) for i in xrange(rolls)]
        return '[%dd%d%s] %s' % (dice, sides, self._formatMod(mod), ', '.join(L))

    def _parseShadowrunRoll(self, m):
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return
        L = [self._roll(1, 6) for i in xrange(rolls)]
        self.log.debug(format("%L", [str(i) for i in L]))
        return self._processSRResults(L, rolls)

    def _parseShadowrunXRoll(self, m):
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return
        L = [self._roll(1, 6) for i in xrange(rolls)]
        self.log.debug(format("%L", [str(i) for i in L]))
        reroll = L.count(6)
        while reroll:
            rerolled = [self._roll(1, 6) for i in xrange(reroll)]
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
