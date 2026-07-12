import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model import Buyer, DoubleAuctionModel, Seller


def test_model_creates_correct_agent_counts():
    model = DoubleAuctionModel(n_buyers=10, n_sellers=8, rng=1)
    buyers = [a for a in model.agents if isinstance(a, Buyer)]
    sellers = [a for a in model.agents if isinstance(a, Seller)]
    assert len(buyers) == 10
    assert len(sellers) == 8
    assert len(model.agents) == 18


def test_sellers_start_with_one_unit_inventory():
    model = DoubleAuctionModel(n_buyers=5, n_sellers=5, rng=1)
    for s in [a for a in model.agents if isinstance(a, Seller)]:
        assert s.inventory == 1


def test_buyers_start_with_zero_inventory():
    model = DoubleAuctionModel(n_buyers=5, n_sellers=5, rng=1)
    for b in [a for a in model.agents if isinstance(a, Buyer)]:
        assert b.inventory == 0


def test_each_agent_schedules_its_own_first_arrival():
    model = DoubleAuctionModel(n_buyers=5, n_sellers=5, rng=1)
    model.run_for(1)
    assert (
        model.cumulative_volume > 0
        or len(model.order_book.bids) > 0
        or len(model.order_book.asks) > 0
    )


def test_run_for_advances_time_and_steps():
    model = DoubleAuctionModel(n_buyers=5, n_sellers=5, rng=1)
    assert model.time == 0.0
    model.run_for(10)
    assert model.time == 10.0


def test_volume_never_exceeds_min_side_size():
    model = DoubleAuctionModel(n_buyers=5, n_sellers=5, rng=1)
    model.run_for(50)
    assert model.cumulative_volume <= 5


def test_datacollector_produces_one_row_per_tick():
    model = DoubleAuctionModel(n_buyers=10, n_sellers=10, rng=1)
    model.run_for(10)
    model_df = model.datacollector.get_model_vars_dataframe()
    agent_df = model.datacollector.get_agent_vars_dataframe()
    assert len(model_df) == 10
    assert len(agent_df) == 10 * 20


def test_no_agent_ever_transacts_at_a_loss():
    model = DoubleAuctionModel(n_buyers=20, n_sellers=20, rng=7)
    model.run_for(100)
    for a in model.agents:
        if isinstance(a, Buyer) and a.done_trading:
            assert a.wealth() >= -1e-9  # bought at or below reservation price
        if isinstance(a, Seller) and a.done_trading:
            assert a.cash >= a.private_value - 1e-9  # sold at or above cost


def test_a_done_trading_agent_never_appears_in_the_book_again():
    model = DoubleAuctionModel(n_buyers=15, n_sellers=15, rng=3)
    model.run_for(50)
    resting_ids = {o.agent_id for o in model.order_book.bids} | {
        o.agent_id for o in model.order_book.asks
    }
    done_ids = {a.unique_id for a in model.agents if a.done_trading}
    assert resting_ids.isdisjoint(done_ids)
