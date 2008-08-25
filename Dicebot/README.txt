Description
~~~~~~~~~~~
Dicebot plugin contains the commands which simulate rolling of dice.
Though core supybot plugin Games contain 'dice' command, it is very simple and
is not sufficient for advanced uses, such as online playing of tabletop
role-playing games using IRC.
The most basic feature of any dicebot is, of course, rolling of one or several
identical dice and showing the results. That is what core 'dice' command can
do. It takes an expression such as 3d6 and returns a series of numbers -
results of rolling each (of 3) die (6-sided): '2, 4, and 4'. This may be
sufficient for some games, but usually you need more. Here is what this plugin
can do for you.

Features
~~~~~~~~
1. Sum of dice rolled. Expression form is just '2d6', plugin returns the sum
of dice values as one number.
2. Sum of dice plus some fixed number. Expression: '2d6-2'. After summing up
dice results the specified number is added (or subtracted) to the sum.
3. Separate results of several identical rolls which use previously described
form. This is written as '3#1d20+7' and yields 3 numbers, each meaning the
result of rolling 1d20+7 as described above.
4. Possibility to omit leading 1 as dice count and use just 'd6' or '3#d20'.
5. Two (three?) distinct modes of operation: roll command and autorolling (can
be enabled per-channel and for private messages, see configuration below).
roll command accepts just one expression and shows its result (if the
expression is valid). Autorolling means that bot automatically rolls and
displays all recognized expressions it sees (be it on the channel or in the
query). Autorolling is much more convenient during online play, but may be
confusing during normal talk, so it can be enabled only when it is needed.
6. To distinguish between different rolls, all results are prefixed with
requesting user's nick and requested expression.

Configuration
~~~~~~~~~~~~~
autoRoll (per-channel): whether to roll all expressions seen on the channel
autoRollInPrivate (global): whether to roll expressions in the queries
Both settings are off by default, so that bot replies only to explicit !roll.

To be done
~~~~~~~~~~
Rolling of several expressions from one message (displaying results separately,
but in one reply).
Calculating more advanced expressions: including several dice ('1d12+2d6+4'),
including several modifiers ('1d20+10-3').
Special support for Shadowrun mechanics (more compact expression forms,
calculating hits, recognizing glithes, exploding dice mode).

Thanks
~~~~~~
Ur-DnD roleplaying community (#dnd @ RusNet) for games, talking and fun, and
personally Zuzuzu for describing basic dicebot requirements, which led to
writing the first version of this plugin in August 2007.

