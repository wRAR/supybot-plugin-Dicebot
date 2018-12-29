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

from datetime import date
import pytest
from .money import MoneyConverter, HttpRequester

class TestMoney:
    def test_normalize(self):
        m = MoneyConverter(None)
        assert m.normalize("$") == "USD"
        assert m.normalize("usd") == "USD"
        assert m.normalize("₽") == "RUB"
        assert m.normalize("грн") == "UAH"

    def test_format_money(self):
        m = MoneyConverter(None)
        assert m.format_money(500, "USD") == "$500"
        assert m.format_money(400, "₽") == "400₽"
        assert m.format_money(400, "руб") == "400₽"
        assert m.format_money(200.3, "грн") == "200.30 грн"

    def test_single_currency_straight_reverse(self):
        r = DummyRequester({"UAH_USD":0.04})
        m = MoneyConverter(r)
        assert m.convert(1, "uah", ["usd"]) == "1 uah: $0.04"
        assert r.query_count == 1
        assert r.last_query == "UAH_USD"

        assert m.convert(1, "usd", ["грн"]) == "$1: 25 грн"
        assert r.query_count == 1

    def test_several_currencies(self):
        r = DummyRequester({"UAH_USD":0.04,"UAH_EUR":0.03,"UAH_RUB":2.5})
        m = MoneyConverter(r)
        assert m.convert(1, "uah", ["usd", "eur", "rub"]) == "1 uah: $0.04, €0.03, 2.50₽"
        assert r.query_count == 3

    def test_non_trivial_amount(self):
        r = DummyRequester({"UAH_USD":0.04})
        m = MoneyConverter(r)
        assert m.convert(15, "uah", ["usd"]) == "15 uah: $0.60"
        assert r.query_count == 1
        assert r.last_query == "UAH_USD"

        assert m.convert(25, "usd", ["грн"]) == "$25: 625 грн"
        assert r.query_count == 1

    def test_no_op(self):
        r = DummyRequester({"UAH_USD":0.04})
        m = MoneyConverter(r)
        assert m.convert(1000, "usd", ["usd"]) == "$1000: $1000"
        assert r.query_count == 0

    def test_integration(self):
        r = HttpRequester()
        m = MoneyConverter(r)
        s = m.convert(100, "руб", ["бел"])
        rate = m.cache["RUB_BYN"].rate
        assert s == "100₽: {0:.2f} бел".format(rate * 100)

    def test_cache_expiration(self):
        r = DummyRequester({"UAH_USD":0.04})
        m = MoneyConverter(r)
        assert m.convert(15, "uah", ["usd"]) == "15 uah: $0.60"
        assert r.query_count == 1
        assert r.last_query == "UAH_USD"

        assert m.convert(25, "uah", ["usd"]) == "25 uah: $1"
        assert r.query_count == 1

        m.cache["UAH_USD"].created_at = date(1980, 1, 1)

        assert m.convert(1, "uah", ["usd"]) == "1 uah: $0.04"
        assert r.query_count == 2

class DummyRequester:
    def __init__(self, response):
        self.response = response
        self.last_query = None
        self.query_count = 0

    def request(self, query):
        self.query_count += 1
        self.last_query = query
        return self.response
