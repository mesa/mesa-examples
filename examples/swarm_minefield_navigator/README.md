# Autonomous Swarm Drone Minefield Mapping with Mesa

This repository implements a production-oriented Mesa agent-based model for autonomous minefield mapping under partial observability, battery limits, and strict safety semantics. The system now operates as a heterogeneous, dynamically reconfigurable swarm with checkpoint-based retreat, dead-end collapsing, airborne regrouping, and verified final-path extraction.

## Table of Contents

*   [Running the Example](#running-the-example)
*   [Testing](#testing)
*   [Results](#results)
*   [Mission Overview](#mission-overview)
*   [World Model](#world-model)
*   [Shared Knowledge Model](#shared-knowledge-model)
*   [Agent Roles and Duties](#agent-roles-and-duties)
*   [Drone State Machine](#drone-state-machine)
*   [Standard Protocols](#standard-protocols)
*   [Emergency Protocols](#emergency-protocols)
*   [Leadership Policy](#leadership-policy)
*   [Checkpoint and Dead-End Policy](#checkpoint-and-dead-end-policy)
*   [Path Verification and Final Route Policy](#path-verification-and-final-route-policy)
*   [Time and Battery Model](#time-and-battery-model)
*   [File Layout](#file-layout)

## Running the Example

Create a virtual environment, install dependencies, and launch the server:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

The server selects the first available localhost port starting at `8521`.

## Testing

Run the unit test suite with:

```
python -m unittest discover -s tests -v
```

The current suite covers:

*   mine buffer propagation
*   battery depletion
*   movement radius enforcement
*   final-path marking
*   blocked-goal handling
*   model shutdown on exhausted drones
*   reserved corridor safety
*   dead-end immutability
*   anti-reversal movement policy
*   leadership handoff
*   free-fly promotion

## Results

Placeholder for result images, screenshots, and experiment snapshots.

Add your output figures here, for example:

*   final deep-blue verified path
*   leadership handoff sequence
*   checkpoint creation and checkpoint retirement
*   gray dead-end collapse behavior
*   airborne regroup / rally snapshots

## Mission Overview

The mission objective is to map a continuous safe corridor from the bottom edge of a `100 x 100` minefield to the top edge while respecting:

*   local sensing only
*   one-cell movement per action
*   strict mine and buffer exclusion for ground traversal
*   battery limitations
*   partial observability

The swarm explores, shares discovered terrain knowledge, adapts leadership when a better-positioned drone emerges, retreats from failed branches using checkpoints, permanently closes bad branches as dead ends, and finally runs verified pathfinding to produce the mission corridor.

## World Model

*   Grid size: `100 x 100`
*   Physical interpretation: `100m x 100m`
*   Space type: `mesa.space.MultiGrid(100, 100, False)`
*   Agents:
    *   `MineAgent`
    *   `DroneAgent`
    *   visualization-only markers for knowledge, checkpoints, and dead ends
*   Motion:
    *   drones move exactly one cell per action
    *   Moore-neighborhood movement
    *   non-toroidal boundaries

Safety semantics:

*   `MINE`: lethal cell
*   `UNSAFE_BUFFER`: one-cell safety halo around a known mine
*   `SAFE`: explicitly scanned and clear
*   `DEAD_END`: permanently retired branch
*   `FINAL_PATH`: verified winning route after mission success

Ground movement policy:

*   cannot walk on `MINE`
*   cannot walk on `UNSAFE_BUFFER`
*   cannot walk on `DEAD_END`
*   may walk beside `UNSAFE_BUFFER`

Airborne recovery policy:

*   may fly over `MINE`
*   may fly over `UNSAFE_BUFFER`
*   may fly over `DEAD_END`

## Shared Knowledge Model

The model maintains a global `knowledge_base` that acts as a mesh-network state store shared by all drones.

The swarm begins blind. The map is not pre-populated with mine locations.

### Knowledge States

*   `SAFE`
*   `MINE`
*   `UNSAFE_BUFFER`
*   `FINAL_PATH`
*   `DEAD_END`

### Ground Truth vs Discovered Truth

Ground truth exists only in the actual Mesa grid through `MineAgent` placement.

Drones are not allowed to use hidden mine information for normal movement decisions. They discover terrain through local scans and write the result into `knowledge_base`.

### Scan Mechanism

Each drone scans twice per step:

1.  before movement
2.  after movement

Each scan inspects the inclusive Moore neighborhood of radius `1`, producing a `3 x 3` local sensor footprint:

*   current cell
*   8 surrounding cells

Per scanned cell:

*   if a `MineAgent` exists in that ground-truth cell, the cell is registered as `MINE`
*   otherwise the cell is registered as `SAFE`

After mine discovery:

*   the model propagates `UNSAFE_BUFFER` to all adjacent cells around the mine

Additional scan effects:

*   scanned cells are removed from `verification_queue`
*   frontier neighbors of scanned safe cells are added to `verification_queue`
*   leader-only scan results may produce checkpoints
*   cells already marked `DEAD_END` are skipped and never turned back into blue/safe state

## Agent Roles and Duties

The swarm contains four drones:

*   `1` leader
*   `3` followers

### Leader Duty

The leader is responsible for:

*   driving vertical exploration
*   flanking around hazards
*   creating safe checkpoints
*   detecting soft deadlocks
*   retreating from failed branches
*   collapsing dead-end corridors
*   acting as the main route-forging unit

### Follower Duty

Followers are responsible for:

*   widening the scanned corridor around the leader
*   covering flanks and rear
*   maintaining formation when possible
*   rallying to new leaders after handoff
*   regrouping rapidly during retreat
*   supporting verification density for final path extraction

### Formation Offsets

Follower offsets relative to the leader:

*   left wing: `(-2, -1)`
*   right wing: `(2, -1)`
*   rear guard: `(0, -2)`

## Drone State Machine

Each `DroneAgent` operates through explicit role-aware states.

### `SCANNING`

Normal ground exploration state.

Leader behavior:

*   prefers northward progress
*   falls back to lateral flanking if blocked
*   escalates to retreat when progress fails

Follower behavior:

*   moves toward its leader-relative formation offset
*   uses shared knowledge to avoid known hazards

### `AVOIDING`

Leader local wall-follow state.

Used when the northward lane is blocked but the branch is not yet abandoned.

Behavior:

*   retry north
*   try committed flank direction
*   reverse flank if needed
*   escalate to retreat if no productive move remains

### `BACKTRACKING`

Leader macro-recovery state.

Behavior:

*   select nearest active checkpoint
*   fly back toward it
*   mark every abandoned branch cell as `DEAD_END`
*   if checkpoint is exhausted, retire it and convert it to gray dead-end state
*   if checkpoint reveals a fresh route, return to `SCANNING`

### `RALLYING`

Follower regroup state.

Behavior:

*   move toward leader or leader retreat target
*   use safe movement first when possible
*   use local safe memory for escape from pockets
*   use airborne override when regrouping requires bypassing hazards

### `FREE_FLY`

Short swarm-wide independent search state.

Behavior:

*   temporarily releases all drones from formation
*   used during leader-stuck recovery windows
*   best-progress drone may later become leader

## Standard Protocols

### Per-Step Protocol

For each active drone:

1.  scan local neighborhood
2.  update local safe memory
3.  select next move according to state and role
4.  decrement battery
5.  move one cell if a move was chosen
6.  scan again
7.  register mission time for that action
8.  update leader progress metrics if applicable

### Normal Ground Navigation Policy

During ground navigation:

*   only `SAFE` and `UNEXPLORED` cells are considered traversable
*   `MINE`, `UNSAFE_BUFFER`, and `DEAD_END` are blocked
*   direct back-and-forth reversal is disallowed when an alternative move exists

### Anti-Oscillation Policy

Each drone tracks:

*   `recent_path`
*   `last_position`
*   `local_safe_memory`

The current hard anti-bounce rule prevents an immediate reversal back to the previous cell during non-airborne movement if any other valid move exists.

### Shared Frontier Verification

Scanned safe cells push nearby unknown cells into `verification_queue`.

This queue exists so the swarm can later verify frontier boundaries and avoid building the final route through partially known terrain.

## Emergency Protocols

### Soft Deadlock Detection

The leader tracks:

*   `max_y_reached`
*   `frustration_counter`

If the leader does not improve its best `y` for a sustained period, it is treated as trapped in a horizontal or downward loop even if some legal moves still exist.

### Leader Retreat Protocol

When the leader is judged stuck:

*   the leader enters `BACKTRACKING`
*   selects the nearest active checkpoint
*   flies over hazards to that checkpoint
*   paints abandoned cells as `DEAD_END`
*   if the checkpoint fails, that checkpoint is retired and turned gray
*   retreat continues toward the next checkpoint

### Follower Rubber-Band Regroup

When the leader retreats:

*   followers enter `RALLYING`
*   they stop trying to solve the failed branch as ground navigators
*   they may use airborne override to reach the leader or retreat target

### Leadership Handoff

After scheduler execution, the model evaluates all active drones.

Promotion rule:

*   highest `y` wins
*   tie-breaker uses highest `x`
*   no handoff occurs unless the candidate has strictly better `y` than the current leader

After handoff:

*   old leader becomes follower
*   new leader becomes `LEADER`
*   leader pointer is updated globally
*   follower offsets are reassigned
*   all non-leader drones enter regrouping behavior

### Free-Fly Swarm Release

The model supports a short swarm-wide free-fly mode:

*   drones are temporarily released from formation
*   each tries to gain progress independently
*   after the timer, the best-progress drone may be promoted

## Leadership Policy

The architecture is dynamically heterogeneous.

At any given time:

*   exactly one drone is `LEADER`
*   all others are `FOLLOWER`

Leader responsibilities are operational rather than fixed to a specific agent identity. Leadership is transferable when another drone demonstrates better forward progress.

This prevents the swarm from permanently depending on one trapped drone.

## Checkpoint and Dead-End Policy

### Checkpoint Creation

The leader creates a checkpoint when:

*   its current cell
*   and all 8 local Moore-neighbor cells

are mine-free in the local scan result.

Checkpoints are stored:

*   in `self.model.checkpoints`
*   in `self.model.checkpoint_positions`
*   in the leader's `checkpoint_stack`

### Checkpoint Use

Checkpoints are macro recovery anchors used when a branch fails.

### Checkpoint Retirement

If a leader returns to a checkpoint and still cannot find a fresh forward route:

*   the checkpoint is retired
*   its blue marker is removed
*   it is converted into `DEAD_END`
*   it becomes gray
*   it can never become blue again

### Dead-End Policy

`DEAD_END` means:

*   permanently closed for ground navigation
*   never rescanned into `SAFE`
*   never rewritten as `UNSAFE_BUFFER`
*   still fly-over capable during airborne recovery

## Path Verification and Final Route Policy

The final route is generated only after a drone reaches the top edge.

The model then runs A\* on the discovered safe subgraph.

### Final Path Eligibility

A candidate path cell must:

*   be explicitly `SAFE` or `FINAL_PATH`
*   not be `MINE`
*   not be `UNSAFE_BUFFER`
*   not be `DEAD_END`
*   have all of its Moore neighbors explicitly known

Important rule:

*   adjacent neighbors may be `UNSAFE_BUFFER`
*   the path cell itself cannot be `UNSAFE_BUFFER`

This reflects the intended semantics of the safety buffer: buffers represent forbidden cells, not forbidden adjacency.

### Final Output

If a fully verified route exists:

*   the route is written into `knowledge_base` as `FINAL_PATH`
*   rendered deep blue in the UI
*   the simulation halts

If no verified route exists:

*   the model reports failure gracefully
*   no fabricated route is produced through unknown terrain

### Complexity

Let:

*   `V` = number of explored/verified candidate cells
*   `E` = number of valid Moore-neighborhood edges among them

Then:

*   A\* time complexity: `O((V + E) log V)`
*   A\* space complexity: `O(V)`

Drone local sensing and step-level directional decisions remain bounded by local neighborhoods and are effectively `O(1)` per step with respect to grid size.

## Time and Battery Model

Each drone starts with:

*   `battery = 600`

Battery policy:

*   battery decreases by `1` per drone action
*   when battery reaches `0`, the drone becomes inactive

Mission time policy:

*   normal scan/ground step: `1.0` second per cell
*   airborne recovery / bypass / retreat step: `0.25` second per cell

Elapsed mission time is accumulated explicitly and displayed in the UI.

## File Layout

*   `agents.py`: drone state machine, local scan logic, role policies, anti-oscillation logic, rallying, retreat, airborne override
*   `model.py`: grid construction, mine placement, shared knowledge maintenance, leadership handoff, checkpoint/dead-end management, final A\* path generation
*   `server.py`: Mesa `ModularServer`, `CanvasGrid`, portrayal logic, live swarm status panel
*   `tests/test_model.py`: behavioral tests for hazards, pathfinding, leader handoff, free-fly promotion, dead-end immutability, anti-reversal policy