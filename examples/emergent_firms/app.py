"""FastAPI backend for the Emergent Firm Formation visualization."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from model import FirmModel, FirmScenario, get_firms, get_workers
from agents import Worker, Firm


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
    rng: int = 42


class StepParams(BaseModel):
    steps: int = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _model_timeseries() -> dict:
    """Return all datacollector model-level time-series as lists."""
    df = model.datacollector.get_model_vars_dataframe()
    return {col: df[col].tolist() for col in df.columns}


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
    """Full snapshot returned after init/step."""
    worker_ids = sorted([w.unique_id for w in get_workers(model)])
    return {
        "step": model.steps,
        "timeseries": _model_timeseries(),
        "firms": _firms_summary(),
        "largest_firm_id": _largest_firm_id(),
        "worker_ids": worker_ids,
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
    return _snapshot()


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
    history = model.firm_history.get(firm.unique_id, {"output": [], "free_riders": [], "avg_effort": [], "step": []})

    return {
        "id": firm.unique_id,
        "size": firm.size,
        "output": round(firm.output, 4),
        "age": firm.age,
        "workers": worker_data,
        "internal_edges": internal_edges,
        "history": history,
    }


@app.get("/api/agent/{agent_id}")
async def api_agent(agent_id: int):
    """Detail for one agent: history + friends network."""
    if model is None:
        return {"error": "Model not initialized"}

    # Find the worker
    worker = None
    for w in get_workers(model):
        if w.unique_id == agent_id:
            worker = w
            break
    if worker is None:
        return {"error": f"Agent {agent_id} not found"}

    # History from datacollector (agenttype reporters)
    try:
        agent_df = model.datacollector.get_agenttype_vars_dataframe(Worker)
        if not agent_df.empty and agent_id in agent_df.index.get_level_values("AgentID"):
            agent_rows = agent_df.xs(agent_id, level="AgentID")
            history = {
                "effort": agent_rows["Effort"].tolist(),
                "income": agent_rows["Income"].tolist(),
            }
        else:
            history = {"effort": [], "income": []}
    except Exception:
        history = {"effort": [], "income": []}

    # Friends network
    current_firm = worker.firm
    friends_data = []
    edges = []
    for fr in worker.friends:
        fr_firm = fr.firm
        friends_data.append({
            "id": fr.unique_id,
            "firm_id": fr_firm.unique_id if fr_firm else None,
            "same_firm": (fr_firm == current_firm) if current_firm else False,
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

    # --- Collapsed firms (from firm_history) ---
    for fid, hist in model.firm_history.items():
        if fid not in living_ids and len(hist["output"]) > 0:
            # Use peak size (max output period) as a proxy for historical size
            peak_output = max(hist["output"])
            lifespan = len(hist["step"])
            last_output = hist["output"][-1]
            # Estimate peak size from number of steps with output
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
        "step": model.steps,
        "total_firms": len(firm_data),
        "living_firms": len(living_ids),
        "collapsed_firms": len(firm_data) - len(living_ids),
        "total_workers": len(workers),
        "firms": firm_data,
    }


