import os
import sys

from mesa.visualization import Slider, SolaraViz, make_plot_component

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model import DoubleAuctionModel

model_params = {
    "n_buyers": Slider(label="Number of buyers", value=25, min=2, max=100, step=1),
    "n_sellers": Slider(label="Number of sellers", value=25, min=2, max=100, step=1),
    "max_valuation": Slider(
        label="Max valuation ($)", value=100.0, min=10.0, max=500.0, step=10.0
    ),
    "mean_interarrival": Slider(
        label="Mean time between an agent's arrivals",
        value=1.0,
        min=0.1,
        max=5.0,
        step=0.1,
    ),
}

page = SolaraViz(
    DoubleAuctionModel(n_buyers=25, n_sellers=25),
    [
        make_plot_component("ClearingPrice"),
        make_plot_component("CumulativeVolume"),
        make_plot_component("Spread"),
    ],
    model_params=model_params,
    name="Continuous Double Auction — Zero-Intelligence Traders",
)
