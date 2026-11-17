import random
from pathlib import Path

import dill
from mesa.discrete_space import OrthogonalMooreGrid
from mesa_replay import CacheableModel, CacheState
from model import Schelling, SchellingAgent


class CacheableSchelling(CacheableModel):
    """Schelling model with caching and replay capabilities.

    This wraps the standard Schelling model with Mesa-Replay's CacheableModel,
    allowing simulations to be recorded and replayed. The model behaves like
    a regular Mesa model, but can save its state history to a cache file or
    replay from a previously saved cache.
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
        replay=False,
        verbose=False,
    ):
        """Create a new cacheable Schelling model.

        Args:
            width: Grid width
            height: Grid height
            density: Initial population density
            minority_pc: Fraction of minority agents
            homophily: Minimum similar neighbors needed to be happy
            radius: Neighborhood radius for similarity check
            cache_file_path: Where to save/load the cache file
            replay: If True, replay from cache; if False, record new simulation
            verbose: If True, print status messages
        """
        actual_model = Schelling(
            width=width,
            height=height,
            density=density,
            minority_pc=minority_pc,
            homophily=homophily,
            radius=radius,
        )

        self.verbose = verbose

        cache_path = Path(cache_file_path)
        effective_replay = replay and cache_path.exists() and cache_path.is_file()

        if replay and not effective_replay:
            print(
                f"Cache file not found at {cache_file_path}. "
                "Running in record mode instead."
            )

        cache_state = CacheState.REPLAY if effective_replay else CacheState.RECORD

        if verbose:
            mode = "REPLAY" if cache_state == CacheState.REPLAY else "RECORD"
            print(f"Initializing in {mode} mode")
            print(f"Cache file: {cache_file_path}")

        super().__init__(
            model=actual_model,
            cache_file_path=cache_file_path,
            cache_state=cache_state,
        )

    def step(self):
        """Run one model step. Automatically records or replays based on mode."""
        super().step()

        # Write cache after each step in record mode
        if self._cache_state == CacheState.RECORD:
            self._write_cache_file()

        if self.verbose:
            mode = "REPLAY" if self._cache_state == CacheState.REPLAY else "RECORD"
            print(f"Step {self.step_count} ({mode})")

    def __setattr__(self, key, value):
        """Handle attribute setting. Finalizes cache when model stops running."""
        if key == "running":
            was_running = (
                getattr(self.model, "running", True) if hasattr(self, "model") else True
            )
            if hasattr(self, "model"):
                self.model.__setattr__(key, value)
            else:
                super().__setattr__(key, value)

            if (
                hasattr(self, "_cache_state")
                and was_running
                and not value
                and self._cache_state == CacheState.RECORD
                and not self.run_finished
            ):
                if self.verbose:
                    print(f"Finalizing cache at step {self.step_count}...")
                self.finish_run()
        else:
            super().__setattr__(key, value)

    def _serialize_state(self) -> bytes:
        """Serialize model state for caching.

        Custom implementation needed for Mesa 3.x CellAgent positioning.
        """
        state_dict = self.model.__dict__.copy()

        # Save random number generator state
        state_dict["random_state"] = self.model.random.getstate()
        state_dict.pop("random", None)

        # Serialize agents with cell coordinates (not pos, which is None for CellAgents)
        agents_data = []
        for agent in self.model.agents:
            coord = (
                agent.cell.coordinate if hasattr(agent, "cell") and agent.cell else None
            )
            agents_data.append(
                {
                    "unique_id": agent.unique_id,
                    "type": agent.type,
                    "coord": coord,
                }
            )
        state_dict["agents_data"] = agents_data
        state_dict.pop("agents", None)
        state_dict.pop("_agents", None)
        state_dict.pop("_agents_by_type", None)

        # Save grid contents
        grid_data = {}
        for coord, cell in self.model.grid._cells.items():
            grid_data[coord] = [a.unique_id for a in cell.agents]
        state_dict["grid_data"] = grid_data
        state_dict.pop("grid", None)

        # Save data collector state
        if hasattr(self.model, "datacollector"):
            dc = self.model.datacollector
            state_dict["datacollector_data"] = {
                "model_vars": dc.model_vars.copy(),
                "agent_records": dc._agent_records.copy()
                if hasattr(dc, "_agent_records")
                else {},
            }

        # Save agent ID counter
        state_dict["_next_id"] = (
            self.model.agent_id_counter
            if hasattr(self.model, "agent_id_counter")
            else getattr(self.model, "_next_id", 0)
        )

        return dill.dumps(state_dict)

    def _deserialize_state(self, state: bytes) -> None:
        """Restore model state from cache.

        Custom implementation needed for Mesa 3.x agent management.
        """
        if self.verbose:
            print(f"Restoring state at step {self.step_count}")
        state_dict = dill.loads(state)  # noqa: S301

        # Restore basic attributes first
        for k, v in state_dict.items():
            if k not in [
                "random_state",
                "agents_data",
                "grid_data",
                "datacollector_data",
                "_next_id",
            ]:
                setattr(self.model, k, v)

        # Random
        self.model.random = random.Random()
        self.model.random.setstate(state_dict["random_state"])

        # Grid
        self.model.grid = OrthogonalMooreGrid(
            (self.model.width, self.model.height), torus=True, random=self.model.random
        )

        # Clear existing agents to avoid duplicates
        self.model._agents.clear()
        if hasattr(self.model, "_agents_by_type"):
            self.model._agents_by_type.clear()
        if hasattr(self.model, "_all_agents"):
            self.model._all_agents.clear()

        # Restore agents from cached data
        agent_map = {}
        agents_to_restore = state_dict.get("agents_data", [])

        for a_data in agents_to_restore:
            agent = SchellingAgent(self.model, a_data["type"])
            agent.unique_id = a_data["unique_id"]
            coord = a_data.get("coord")

            # Place agent in its cell
            if coord is not None and coord in self.model.grid._cells:
                cell = self.model.grid._cells[coord]
                agent.cell = cell

            agent_map[a_data["unique_id"]] = agent

        # Restore data collector state
        if "datacollector_data" in state_dict and hasattr(self.model, "datacollector"):
            dc_data = state_dict["datacollector_data"]
            self.model.datacollector.model_vars = dc_data["model_vars"].copy()
            if "agent_records" in dc_data and hasattr(
                self.model.datacollector, "_agent_records"
            ):
                self.model.datacollector._agent_records = dc_data[
                    "agent_records"
                ].copy()

        # Restore agent ID counter
        self.model.agent_id_counter = state_dict.get("_next_id", 0)
