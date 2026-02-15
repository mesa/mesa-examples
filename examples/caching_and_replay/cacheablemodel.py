from mesa_replay import CacheableModel, CacheState
from model import Schelling


class CacheableSchelling(CacheableModel):
    """A wrapper around the original Schelling model to make the simulation cacheable
    and replay-able.  Uses CacheableModel from the Mesa-Replay library,
    which is a wrapper that can be put around any regular mesa model to make it
    "cacheable".
    From outside, a CacheableSchelling instance can be treated like any
    regular Mesa model.
    The only difference is that the model will write the state of every simulation step
    to a cache file or when in replay mode use a given cache file to replay that cached
    simulation run.
    """

    def __init__(
        self,
        width=20,
        height=20,
        density=0.8,
        minority_pc=0.2,
        homophily=3,
        radius=1,
        cache_file_path="./my_cache_file_path.cache",
        # Note that this is an additional parameter we add to our model,
        # which decides whether to simulate or replay
        replay=False,
    ):
        actual_model = Schelling(
            width=width,
            height=height,
            density=density,
            minority_pc=minority_pc,
            homophily=homophily,
            radius=radius,
        )
        cache_state = CacheState.REPLAY if replay else CacheState.RECORD
        super().__init__(
            model=actual_model,
            cache_file_path=cache_file_path,
            cache_state=cache_state,
        )
