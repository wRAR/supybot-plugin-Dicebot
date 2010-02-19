###
# Copyright (c) 2007-2010, Andrey Rahmatullin
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

from supybot.commands import additional, wrap
from supybot.utils.str import format, ordinal
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks

class Dicebot(callbacks.Plugin):
    """This plugin supports rolling the dice using !roll 4d20+3 as well as
    automatically rolling such combinations it sees in the channel (if
    autoRoll option is enabled for that channel) or query (if
    autoRollInPrivate option is enabled).
    """

    rollReStandard = re.compile(r'((?P<rolls>\d+)#)?(?P<dice>\d*)d(?P<sides>\d+)(?P<mod>[+-]\d+)?$')
    rollReSR       = re.compile(r'(?P<rolls>\d+)#sd$')
    rollReSRX      = re.compile(r'(?P<rolls>\d+)#sdx$')
    rollReSRE      = re.compile(r'(?P<pool>\d+),(?P<thr>\d+)#sde$')
    rollRe7Sea     = re.compile(r'((?P<count>\d+)#)?(?P<prefix>-|\+)?(?P<rolls>\d+)(?P<k>k{1,2})(?P<keep>\d+)(?P<mod>[+-]\d+)?$')
    rollReWoD      = re.compile(r'(?P<rolls>\d+)w(?P<explode>\d|-)?$')
    rollReDH       = re.compile(r'(?P<rolls>\d*)vs\((?P<thr>([-+]|\d)+)\)$')

    MAX_DICE = 1000
    MIN_SIDES = 2
    MAX_SIDES = 100
    MAX_ROLLS = 30

    def __init__(self, irc):
        super(Dicebot, self).__init__(irc)
        self.deck = Deck()

    def _roll(self, dice, sides, mod=0):
        """
        Roll a die several times, return sum of the results plus the static modifier.

        Arguments:
        dice -- number of dice rolled;
        sides -- number of sides each die has;
        mod -- number added to the total result (optional);
        """
        res = int(mod)
        for i in xrange(dice):
            res += random.randrange(1, sides+1)
        return res

    def _rollMultiple(self, dice, sides, rolls=1, mod=0):
        """
        Roll several dice several times, return a list of results.

        Specified number of dice with specified sides is rolled several times.
        Each time the sum of results is calculated, with optional modifier
        added. The list of these sums is returned.

        Arguments:
        dice -- number of dice rolled each time;
        sides -- number of sides each die has;
        rolls -- number of times dice are rolled;
        mod -- number added to the each total result (optional);
        """
        return [self._roll(dice, sides, mod) for i in xrange(rolls)]

    def _formatMod(self, mod):
        """
        Format a numeric modifier for printing expressions such as 1d20+3.

        Nonzero numbers are formatted with a sign, zero is formatted as an
        empty string.
        """
        return ('%+d' % mod) if mod != 0 else ''

    def _process(self, irc, text):
        """
        Process a message and reply with roll results, if any.

        The message is split to the words and each word is checked against all
        known expression forms (first applicable form is used). All results
        are printed together in the IRC reply.
        """
        checklist = [
                (self.rollReStandard, self._parseStandardRoll),
                (self.rollReSR, self._parseShadowrunRoll),
                (self.rollReSRX, self._parseShadowrunXRoll),
                (self.rollReSRE, self._parseShadowrunExtRoll),
                (self.rollRe7Sea, self._parse7SeaRoll),
                (self.rollReWoD, self._parseWoDRoll),
                (self.rollReDH, self._parseDHRoll),
                ]
        results = [ ]
        for word in text.split():
            for expr, parser in checklist:
                m = expr.match(word)
                if m:
                    r = parser(m)
                    if r:
                        results.append(r)
                        break
        if results:
            irc.reply('; '.join(results))

    def _parseStandardRoll(self, m):
        """
        Parse rolls such as 3#2d6+2.

        This is a roll (or several rolls) of several dice with an optional
        static modifier. It yields one number (the sum of results and
        modifier) for each roll series.
        """
        rolls = int(m.group('rolls') or 1)
        dice = int(m.group('dice') or 1)
        sides = int(m.group('sides'))
        mod = int(m.group('mod') or 0)
        if (dice > self.MAX_DICE or sides > self.MAX_SIDES
            or sides < self.MIN_SIDES or rolls < 1 or rolls > self.MAX_ROLLS):
            return
        L = self._rollMultiple(dice, sides, rolls, mod)
        return '[%dd%d%s] %s' % (dice, sides, self._formatMod(mod),
                                 ', '.join([str(i) for i in L]))

    def _parseShadowrunRoll(self, m):
        """
        Parse Shadowrun-specific roll such as 3#sd.
        """
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_DICE:
            return
        L = self._rollMultiple(1, 6, rolls)
        self.log.debug(format("%L", [str(i) for i in L]))
        return self._processSRResults(L, rolls)

    def _parseShadowrunXRoll(self, m):
        """
        Parse Shadowrun-specific 'exploding' roll such as 3#sdx.
        """
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_DICE:
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
            hitsStr = format('%n', (hits, 'hit'))
            glitchStr = ', glitch' if isGlitch else ''
            return '(pool %d%s) %s%s' % (pool, explStr, hitsStr, glitchStr)
        if isGlitch:
            return '(pool %d%s) critical glitch!' % (pool, explStr)
        return '(pool %d%s) 0 hits' % (pool, explStr)

    def _parseShadowrunExtRoll(self, m):
        """
        Parse Shadowrun-specific Extended test roll such as 14,3#sde.
        """
        pool = int(m.group('pool'))
        if pool < 1 or pool > self.MAX_DICE:
            return
        threshold = int(m.group('thr'))
        if threshold < 1 or threshold > self.MAX_DICE:
            return
        result = 0
        passes = 0
        glitches = []
        critGlitch = None
        while result < threshold:
            L = self._rollMultiple(1, 6, pool)
            self.log.debug(format('%L', [str(i) for i in L]))
            hits = L.count(6) + L.count(5)
            result += hits
            passes += 1
            isHit = hits > 0
            isGlitch = L.count(1) >= (pool + 1) / 2
            if isGlitch:
                if not isHit:
                    critGlitch = passes
                    break
                glitches.append(ordinal(passes))

        glitchStr = format(', glitch at %L', glitches) if len(glitches) > 0 else ''
        if critGlitch is None:
            return format('(pool %i, threshold %i) %n, %n%s',
                          pool, threshold, (passes, 'pass'), (result, 'hit'), glitchStr)
        else:
            return format('(pool %i, threshold %i) critical glitch at %s pass%s, %n so far',
                          pool, threshold, ordinal(critGlitch), glitchStr, (result, 'hit'))

    def _parse7SeaRoll(self, m):
        """
        Parse 7th Sea-specific roll (4k2 is its simplest form).
        """
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return
        count = int(m.group('count') or 1)
        keep = int(m.group('keep'))
        mod = int(m.group('mod') or 0)
        prefix = m.group('prefix')
        k = m.group('k')
        explode = prefix != '-'
        if keep < 1 or keep > self.MAX_ROLLS:
            return
        if keep > rolls:
            keep = rolls
        if rolls > 10:
            keep += rolls - 10
            rolls = 10
        if keep > 10:
            mod += (keep - 10) * 10
            keep = 10
        unkept = (prefix == '+' or k == 'kk') and keep < rolls
        explodeStr = ', not exploding' if not explode else ''
        results = []
        for _ in xrange(count):
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
            keptDice, unkeptDice = L[:keep], L[keep:]
            unkeptStr = ' | %s' % ', '.join([str(i) for i in unkeptDice]) if unkept else ''
            keptStr = ', '.join([str(i) for i in keptDice])
            results.append('(%d) %s%s' % (sum(keptDice) + mod, keptStr, unkeptStr))

        return '[%dk%d%s%s] %s' % (rolls, keep, self._formatMod(mod), explodeStr,
                                   '; '.join(results))


    def _parseWoDRoll(self, m):
        """
        Parse New World of Darkness roll (5w)
        """
        rolls = int(m.group('rolls'))
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return
        if m.group('explode') == '-':
            explode = 0
        elif m.group('explode') != None and m.group('explode').isdigit():
            explode = int(m.group('explode'))
            if explode < 8 or explode > 10:
                explode = 10
        else:
            explode = 10
        L = self._rollMultiple(1, 10, rolls)
        self.log.debug(format("%L", [str(i) for i in L]))
        successes = len([x for x in L if x >= 8])
        if explode:
            for i in xrange(len(L)):
                if L[i] >= explode:
                    while True:
                        rerolled = self._roll(1, 10)
                        self.log.debug(str(rerolled))
                        if rerolled >= 8:
                            successes += 1
                        if rerolled < explode:
                            break

        if explode == 0:
            explStr = ', not exploding'
        elif explode != 10:
            explStr = ', %d-again' % explode
        else:
            explStr = ''

        result = format('%n', (successes, 'success')) if successes > 0 else 'FAIL'
        return '(%d%s) %s' % (rolls, explStr, result)

    def _parseDHRoll(self, m):
        """
        Parse Dark Heresy roll (3vs(20+30-10))
        """
        rolls = int(m.group('rolls') or 1)
        if rolls < 1 or rolls > self.MAX_ROLLS:
            return

        thresholdExpr = m.group('thr')
        # additional validation
        if not re.match(r'^[+\-]?\d{1,4}([+\-]\d{1,4})*$', thresholdExpr):
            return

        threshold = eval(thresholdExpr)
        rollResults = self._rollMultiple(1, 100, rolls)
        results = [threshold - roll for roll in rollResults]
        return '%s (%s vs %d)' % (', '.join([str(i) for i in results]),
                                  ', '.join([str(i) for i in rollResults]),
                                  threshold)

    def _autoRollEnabled(self, irc, channel):
        """
        Check if automatic rolling is enabled for this context.
        """
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

        Restores and shuffles the deck.
        """
        self.deck.shuffle()
        irc.reply('shuffled')
    shuffle = wrap(shuffle)

    def draw(self, irc, msg, args, count):
        """[<count>]

        Draws <count> cards (1 if omitted) from the deck and shows them.
        """
        cards = [self.deck.next() for i in xrange(count)]
        irc.reply(', '.join(cards))
    draw = wrap(draw, [additional('positiveInt', 1)])
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
