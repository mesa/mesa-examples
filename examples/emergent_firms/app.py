"""FastAPI backend for the Emergent Firm Formation visualization."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from emergent_firms.model import FirmModel, FirmScenario, get_firms, get_workers
from emergent_firms.agents import Worker, Firm


# ---------------------------------------------------------------------------
# Global model state
# ---------------------------------------------------------------------------
model: FirmModel | None = None


class InitParams(BaseModel):
    num_agents: int = 1000
    a: float = 1.0
    b: float = 1.0
    beta: float = 2.0
    num_friends: int = 2
    make_friends: bool = False
    max_friends: int = 10
    rng: int = 42


class StepParams(BaseModel):
    steps: int = 1
    since_step: int | None = None
    active_tab: str | None = None
    rc_metric: str = "size"
    rc_top_n: int = 25
    agent_id: int | None = None


# Series plotted by the 4 Model-tab charts
_CHART_SERIES = (
    "Number of Firms",
    "New Firms",
    "Average Firm Size",
    "Largest Firm Size",
    "Total Output",
    "Output Largest Firm",
    "Average Effort Overall",
    "Average Effort Largest Firm",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_step() -> int:
    """Authoritative simulation period count (immune to wrapper double-increments)."""
    return getattr(model, "_period", model.steps)


def _model_timeseries() -> dict:
    """Return all datacollector model-level time-series directly from model_vars (no DataFrame copy)."""
    model_vars = getattr(model.datacollector, "model_vars", None)
    if model_vars is not None:
        return {col: list(vals) for col, vals in model_vars.items()}
    df = model.datacollector.get_model_vars_dataframe()
    return {col: df[col].tolist() for col in df.columns}


def _timeseries_delta(since_step: int) -> dict:
    """Return only newly collected values after since_step (skipping step 0)."""
    start = max(1, since_step + 1)
    end = _current_step() + 1
    model_vars = model.datacollector.model_vars
    return {col: model_vars[col][start:end] for col in _CHART_SERIES}


def _firms_summary() -> list[dict]:
    """Return [{id, size, output, age}, ...] sorted by size desc."""
    firms = get_firms(model)
    return sorted(
        [{"id": f.unique_id, "size": f.size, "output": round(f.output, 4), "age": f.age} for f in firms],
        key=lambda x: x["size"],
        reverse=True,
    )


def _largest_firm_id() -> int | None:
    firms = get_firms(model)
    if not firms:
        return None
    return max(firms, key=lambda f: f.size).unique_id


def _snapshot() -> dict:
    """Full snapshot returned after init/reset (and legacy step calls)."""
    worker_ids = sorted([w.unique_id for w in get_workers(model)])
    firms = get_firms(model)
    return {
        "step": _current_step(),
        "num_firms": len(firms),
        "timeseries": _model_timeseries(),
        "firms": _firms_summary(),
        "largest_firm_id": _largest_firm_id(),
        "worker_ids": worker_ids,
    }


def _rank_clock_delta(since_step: int, metric: str, top_n: int, total_living_firms: int) -> dict:
    """Return O(delta_steps) rank-clock incremental update for steps (since_step + 1)..current_step."""
    step = _current_step()
    metric_key = "output" if metric == "output" else "size"
    top_n = max(5, min(100, top_n))
    snapshots = model.rank_snapshots.get(metric_key, [])

    # snapshots[0] corresponds to step 1
    start_idx = max(0, since_step)
    new_slices = [
        [list(item) for item in step_top[:top_n]]
        for step_top in snapshots[start_idx:step]
    ]

    dissolved_ids: list[int] = []
    dissolved_by_step = getattr(model, "dissolved_by_step", None)
    if dissolved_by_step is not None:
        for step_dissolved in dissolved_by_step[start_idx:step]:
            if step_dissolved:
                dissolved_ids.extend(step_dissolved)

    return {
        "since_step": since_step,
        "step": step,
        "metric": metric_key,
        "top_n": top_n,
        "total_living_firms": total_living_firms,
        "new_steps": new_slices,
        "dissolved_ids": dissolved_ids,
    }


def _agent_payload(agent_id: int, since_step: int | None = None) -> dict:
    """Build O(1) detail or incremental delta for one worker."""
    step = _current_step()
    workers_by_id = getattr(model, "workers_by_id", None)
    if workers_by_id is not None:
        worker = workers_by_id.get(agent_id)
    else:
        worker = next((w for w in get_workers(model) if w.unique_id == agent_id), None)

    if worker is None:
        return {"error": f"Agent {agent_id} not found"}

    if hasattr(worker, "effort_history"):
        if since_step is not None:
            start = max(0, since_step + 1)
            history = {
                "since_step": since_step,
                "effort_delta": worker.effort_history[start : step + 1],
                "income_delta": worker.income_history[start : step + 1],
            }
        else:
            history = {
                "effort": worker.effort_history,
                "income": worker.income_history,
            }
    else:
        history = {"effort": [], "income": []}

    current_firm = worker.firm
    friends_data = []
    edges = []
    for fr in worker.friends:
        fr_firm = fr.firm
        friends_data.append({
            "id": fr.unique_id,
            "firm_id": fr_firm.unique_id if fr_firm else None,
            "same_firm": (fr_firm == current_firm) if (current_firm is not None and fr_firm is not None) else False,
        })
        edges.append({"source": agent_id, "target": fr.unique_id})

    return {
        "id": agent_id,
        "theta": round(worker.theta, 4),
        "effort": round(worker.effort, 4),
        "income": round(worker.income, 4),
        "utility": round(worker.utility, 4),
        "firm_id": current_firm.unique_id if current_firm else None,
        "num_friends": len(worker.friends),
        "history": history,
        "friends": friends_data,
        "edges": edges,
    }


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.post("/api/init")
async def api_init(params: InitParams):
    global model
    scenario = FirmScenario(
        num_agents=params.num_agents,
        a=params.a,
        b=params.b,
        beta=params.beta,
        num_friends=params.num_friends,
        make_friends=params.make_friends,
        max_friends=params.max_friends,
        rng=params.rng,
    )
    model = FirmModel(scenario=scenario)
    return _snapshot()


@app.post("/api/step")
async def api_step(params: StepParams):
    if model is None:
        return {"error": "Model not initialized"}
    for _ in range(params.steps):
        model.step()

    if params.since_step is None:
        return _snapshot()

    num_firms_now = len(get_firms(model))
    resp: dict = {
        "step": _current_step(),
        "since_step": params.since_step,
        "num_firms": num_firms_now,
        "ts_delta": _timeseries_delta(params.since_step),
    }
    if params.active_tab == "firm":
        resp["rc_delta"] = _rank_clock_delta(
            params.since_step,
            params.rc_metric,
            params.rc_top_n,
            num_firms_now,
        )
    elif params.active_tab == "agent" and params.agent_id is not None:
        resp["agent_delta"] = _agent_payload(params.agent_id, since_step=params.since_step)
    return resp


@app.post("/api/reset")
async def api_reset():
    global model
    if model is None:
        return {"error": "Model not initialized"}
    # Re-create with same scenario parameters
    scenario = FirmScenario(
        num_agents=model.num_agents,
        a=model.a,
        b=model.b,
        beta=model.beta,
        num_friends=model.num_friends,
        make_friends=model.make_friends,
        max_friends=model.max_friends,
        rng=42,
    )
    model = FirmModel(scenario=scenario)
    return _snapshot()


@app.get("/api/firms")
async def api_firms():
    if model is None:
        return {"error": "Model not initialized"}
    return _firms_summary()


@app.get("/api/firm/{firm_id}")
async def api_firm(firm_id: int):
    """Detail for one firm: workers + internal friend edges."""
    if model is None:
        return {"error": "Model not initialized"}

    # Find the firm
    firm = None
    for f in get_firms(model):
        if f.unique_id == firm_id:
            firm = f
            break
    if firm is None:
        return {"error": f"Firm {firm_id} not found"}

    workers = list(firm.workers)
    worker_ids = {w.unique_id for w in workers}

    worker_data = []
    internal_edges = []
    for w in workers:
        worker_data.append({
            "id": w.unique_id,
            "effort": round(w.effort, 4),
            "income": round(w.income, 4),
            "utility": round(w.utility, 4),
            "theta": round(w.theta, 4),
            "num_friends": len(w.friends),
        })
        # Edges to friends who are also in this firm
        for fr in w.friends:
            if fr.unique_id in worker_ids:
                internal_edges.append({"source": w.unique_id, "target": fr.unique_id})

    # Per-firm history (full life of this firm)
    history = model.firm_history.get(
        firm.unique_id,
        {"size": [], "output": [], "free_riders": [], "avg_effort": [], "step": []},
    )

    return {
        "id": firm.unique_id,
        "size": firm.size,
        "output": round(firm.output, 4),
        "age": firm.age,
        "workers": worker_data,
        "internal_edges": internal_edges,
        "history": history,
    }


@app.get("/api/rank_clock")
async def api_rank_clock(metric: str = "size", top_n: int = 25):
    """Return firm rank trajectories over time for the Rank Clock visualization."""
    if model is None:
        return {"error": "Model not initialized"}

    metric_key = "output" if metric == "output" else "size"
    top_n = max(5, min(100, top_n))

    snapshots = model.rank_snapshots.get(metric_key, [])
    living_map = {f.unique_id: f for f in get_firms(model)}

    # Assemble per-firm trajectories across steps 1..T
    # Each point is [step, rank, size, output]
    trajectories: dict[int, dict] = {}
    rank1_turnovers = 0
    prev_rank1_id: int | None = None

    for step_idx, step_top in enumerate(snapshots):
        step_num = step_idx + 1
        sliced = step_top[:top_n]
        if sliced:
            r1_id = sliced[0][0]
            if prev_rank1_id is not None and r1_id != prev_rank1_id:
                rank1_turnovers += 1
            prev_rank1_id = r1_id

        for rank_idx, (fid, size, output, age) in enumerate(sliced):
            rank = rank_idx + 1
            entry = trajectories.get(fid)
            if entry is None:
                entry = {
                    "id": fid,
                    "peak_rank": rank,
                    "peak_size": size,
                    "peak_output": output,
                    "first_step": step_num,
                    "last_step": step_num,
                    "last_age": age,
                    "points": [],
                }
                trajectories[fid] = entry
            else:
                if rank < entry["peak_rank"]:
                    entry["peak_rank"] = rank
                if size > entry["peak_size"]:
                    entry["peak_size"] = size
                if output > entry["peak_output"]:
                    entry["peak_output"] = output
                entry["last_step"] = step_num
                entry["last_age"] = age

            entry["points"].append([step_num, rank, size, output])

    current_ranks: dict[int, int] = {}
    if snapshots:
        for rank_idx, (fid, _, _, _) in enumerate(snapshots[-1][:top_n]):
            current_ranks[fid] = rank_idx + 1

    firms_out = []
    firm_peaks = getattr(model, "firm_peaks", None)
    for fid, entry in trajectories.items():
        living_firm = living_map.get(fid)
        alive = living_firm is not None
        pk = firm_peaks.get(fid) if firm_peaks is not None else None
        if pk is not None:
            total_peak_size = max(pk[0], entry["peak_size"])
            total_peak_output = max(pk[1], entry["peak_output"])
            lifespan = living_firm.age if alive else pk[2]
        else:
            hist = model.firm_history.get(fid)
            total_peak_size = max(hist["size"]) if hist and hist.get("size") else entry["peak_size"]
            total_peak_output = max(hist["output"]) if hist and hist.get("output") else entry["peak_output"]
            lifespan = living_firm.age if alive else (len(hist["step"]) if hist else entry["last_age"])

        firms_out.append({
            "id": fid,
            "alive": alive,
            "in_top_n_now": fid in current_ranks,
            "current_rank": current_ranks.get(fid),
            "current_size": living_firm.size if alive else 0,
            "current_output": round(living_firm.output, 4) if alive else 0.0,
            "age": lifespan,
            "peak_rank": entry["peak_rank"],
            "peak_size": total_peak_size,
            "peak_output": round(total_peak_output, 4),
            "steps_in_top_n": len(entry["points"]),
            "first_step": entry["first_step"],
            "last_step": entry["last_step"],
            "points": entry["points"],
        })

    # Sort: currently in top_n first (by current_rank asc), then historical by peak_rank asc & longevity desc
    firms_out.sort(
        key=lambda x: (
            0 if x["current_rank"] is not None else 1,
            x["current_rank"] if x["current_rank"] is not None else 9999,
            x["peak_rank"],
            -x["steps_in_top_n"],
        )
    )

    return {
        "step": _current_step(),
        "metric": metric_key,
        "top_n": top_n,
        "total_living_firms": len(living_map),
        "rank1_turnovers": rank1_turnovers,
        "last_rank1_id": prev_rank1_id,
        "firms": firms_out,
    }


@app.get("/api/agent/{agent_id}")
async def api_agent(agent_id: int):
    """Detail for one agent: history + friends network."""
    if model is None:
        return {"error": "Model not initialized"}
    return _agent_payload(agent_id, since_step=None)


@app.get("/api/results")
async def api_results():
    """Aggregate end-of-simulation data for the results page."""
    if model is None:
        return {"error": "Model not initialized"}

    firms = get_firms(model)
    workers = get_workers(model)

    # --- Living firms ---
    living_ids = set()
    firm_data = []
    for f in firms:
        living_ids.add(f.unique_id)
        firm_data.append({
            "id": f.unique_id,
            "size": f.size,
            "output": round(f.output, 4),
            "productivity": round(f.output / f.size, 4) if f.size > 0 else 0.0,
            "age": f.age,
            "alive": True,
        })

    # --- Collapsed firms (from firm_history / O(1) firm_peaks) ---
    firm_peaks = getattr(model, "firm_peaks", None)
    for fid, hist in model.firm_history.items():
        if fid not in living_ids and len(hist["output"]) > 0:
            pk = firm_peaks.get(fid) if firm_peaks is not None else None
            peak_output = pk[1] if pk is not None else max(hist["output"])
            lifespan = pk[2] if pk is not None else len(hist["step"])
            last_output = hist["output"][-1]
            firm_data.append({
                "id": fid,
                "size": 0,
                "output": round(last_output, 4),
                "peak_output": round(peak_output, 4),
                "productivity": 0.0,
                "age": lifespan,
                "alive": False,
            })

    firm_data.sort(key=lambda x: x["size"], reverse=True)

    return {
        "step": _current_step(),
        "total_firms": len(firm_data),
        "living_firms": len(living_ids),
        "collapsed_firms": len(firm_data) - len(living_ids),
        "total_workers": len(workers),
        "firms": firm_data,
    }


