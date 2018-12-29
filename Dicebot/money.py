###
# Copyright (c) 2008, Anatoly Popov
# Copyright (c) 2008, Andrey Rahmatullin
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

import requests
import datetime


class HttpRequester:
    def request(self, key):
        r = requests.get("https://free.currencyconverterapi.com/api/v6/convert?q={0}&compact=ultra".format(key))
        return r.json()


class CachedRate:
    def __init__(self, rate):
        self.rate = rate
        self.created_at = datetime.datetime.utcnow().date()


class MoneyConverter:
    """
    Conversion rate bot

    Requests https://free.currencyconverterapi.com/ and cache value for a day
    """

    def __init__(self, requester):
        self.requester = requester
        self.cache = {}
        self.synonims = {
            "₽": "RUB",
            "РУБ": "RUB",
            "Р.": "RUB",

            "ГРН": "UAH",
            "₴": "UAH",

            "Б.Р.": "BYN",
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
            "¥": "JPY",
            "元": "CNY"
        }
        self.output_formats = {
            "USD": "${0}",
            "RUB": "{0}₽",
            "EUR": "€{0}",
            "GBP": "£{0}",
            "UAH": "₴{0}"
        }

    def get_rate_from_origin(self, input_currency, output_currency):
        query = "{0}_{1}".format(input_currency, output_currency)
        result = self.requester.request(query)
        return result[query]

    def get_rates(self, input_currency, output_currencies):
        def request(input, output):
            key = "{0}_{1}".format(input, output)
            rate = self.get_rate_from_origin(input, output)
            result = self.cache[key] = CachedRate(rate)

            inverted_key = "{1}_{0}".format(input, output)
            self.cache[inverted_key] = CachedRate(1 / rate)
            return result

        result = {}
        utc_date = datetime.datetime.utcnow().date()
        input = self.normalize(input_currency)
        for cur in output_currencies:
            output = self.normalize(cur)
            if input == output:
                result[cur] = 1
                continue

            key = "{0}_{1}".format(input, output)
            if key in self.cache:
                cached_rate = self.cache[key]
                if cached_rate.created_at != utc_date:
                    cached_rate = request(input, output)
            else:
                cached_rate = request(input, output)

            result[cur] = cached_rate.rate
        return result

    def normalize(self, cur):
        cur = cur.upper()
        return self.synonims[cur] if cur in self.synonims else cur

    def format_money(self, amount, cur):
        norm = self.normalize(cur)
        output_format = self.output_formats[norm] if norm in self.output_formats else "{0} " + cur
        return output_format.format(int(amount) if isinstance(amount, int) or amount.is_integer() else "{0:.2f}".format(amount))

    def convert(self, amount, input, output):
        rates = self.get_rates(input, output)
        return "{0}: {1}".format(
            self.format_money(amount, input),
            ', '.join(self.format_money(val * amount, key) for (key, val) in rates.items()))
