import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.order_book import OrderBook


def test_no_match_when_bid_below_ask():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=10.0, time=0.0)
    book.submit_ask(agent_id=2, price=20.0, time=0.0)
    assert book.try_match(time=0.0) is None
    assert len(book.bids) == 1
    assert len(book.asks) == 1


def test_match_when_bid_crosses_ask():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=25.0, time=0.0)
    book.submit_ask(agent_id=2, price=15.0, time=0.0)
    trade = book.try_match(time=0.0)
    assert trade is not None
    assert trade.price == 20.0  # midpoint
    assert trade.buyer_id == 1
    assert trade.seller_id == 2
    assert len(book.bids) == 0
    assert len(book.asks) == 0


def test_best_bid_picks_highest_price():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=10.0, time=0.0)
    book.submit_bid(agent_id=2, price=30.0, time=0.0)
    book.submit_bid(agent_id=3, price=20.0, time=0.0)
    assert book.best_bid().price == 30.0


def test_best_bid_uses_earliest_order_as_tie_breaker():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=30.0, time=2.0)
    book.submit_bid(agent_id=2, price=30.0, time=1.0)
    assert book.best_bid().agent_id == 2


def test_best_ask_picks_lowest_price():
    book = OrderBook()
    book.submit_ask(agent_id=1, price=50.0, time=0.0)
    book.submit_ask(agent_id=2, price=10.0, time=0.0)
    book.submit_ask(agent_id=3, price=30.0, time=0.0)
    assert book.best_ask().price == 10.0


def test_best_ask_uses_earliest_order_as_tie_breaker():
    book = OrderBook()
    book.submit_ask(agent_id=1, price=10.0, time=2.0)
    book.submit_ask(agent_id=2, price=10.0, time=1.0)
    assert book.best_ask().agent_id == 2


def test_clear_all_crosses_matches_multiple_pairs():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=50.0, time=0.0)
    book.submit_bid(agent_id=2, price=40.0, time=0.0)
    book.submit_ask(agent_id=3, price=10.0, time=0.0)
    book.submit_ask(agent_id=4, price=20.0, time=0.0)
    trades = book.clear_all_crosses(time=0.0)
    assert len(trades) == 2
    assert len(book.bids) == 0
    assert len(book.asks) == 0


def test_cancel_agent_order_removes_only_that_agents_order():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=10.0, time=0.0)
    book.submit_bid(agent_id=2, price=20.0, time=0.0)
    book.cancel_agent_order(agent_id=1, side="bid")
    assert len(book.bids) == 1
    assert book.bids[0].agent_id == 2


def test_cancel_agent_order_is_a_noop_if_agent_has_no_order():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=10.0, time=0.0)
    book.cancel_agent_order(agent_id=999, side="bid")  # agent 999 never quoted
    assert len(book.bids) == 1


def test_agent_can_replace_its_own_resting_order():
    # This is the core operation continuous re-quoting relies on:
    # cancel your stale order, then submit a fresh one.
    book = OrderBook()
    book.submit_bid(agent_id=1, price=10.0, time=0.0)
    book.cancel_agent_order(agent_id=1, side="bid")
    book.submit_bid(agent_id=1, price=15.0, time=1.0)
    assert len(book.bids) == 1
    assert book.bids[0].price == 15.0


def test_spread_is_ask_minus_bid():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=40.0, time=0.0)
    book.submit_ask(agent_id=2, price=55.0, time=0.0)
    assert book.spread() == 15.0


def test_spread_none_when_book_one_sided():
    book = OrderBook()
    book.submit_bid(agent_id=1, price=40.0, time=0.0)
    assert book.spread() is None
