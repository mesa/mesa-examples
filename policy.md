# Mesa-Examples policy

## Mesa 4 Transition
### Context
Mesa 4 introduces many breaking changes: removal of `DataCollector`, `batch_run`, `seed` parameter, `model.step()` deprecation, space architecture overhaul, new data collection system, and more. Our example models live in two places:

- **Core examples** (`mesa/examples/`): Fully tested, shipped with Mesa, always up to date. Not covered by this policy.
- **User examples** (`mesa-examples`): Community-contributed, tested in CI via smoke tests. **This policy covers these.**

All user examples currently work with Mesa 3.5. Our goal is to bring as many as feasible to Mesa 4, while keeping the process manageable and not blocking Mesa development.

### Branching Strategy
We use a **branch-based compatibility model**:

| Branch | Compatible with | Status |
|---|---|---|
| `main` | Latest Mesa (currently 3.x, then 4.x after release) | Active development |
| `mesa-3.x` | Mesa 3.x releases | Created from `main` before first Mesa 4 breaking merge. Maintained for reference, no active development. |
| `mesa-2.x` | Mesa 2.x releases | Already exists. Archived/read-only. |

**Before the first Mesa 4 breaking change lands on `mesa-examples` `main`**, we create the `mesa-3.x` branch as a snapshot. This preserves all working Mesa 3 examples for users who haven't migrated yet.

After branching, `main` tracks Mesa 4 (and the latest Mesa development branch). Examples on `main` must work with the latest Mesa.

## Responsibility Model for Breaking PRs

When a PR in `mesa/mesa` breaks user examples in `mesa-examples`:

#### PR author responsibilities
1. **Check impact**: Run the mesa-examples smoke tests against your branch (CI does this automatically).
2. **Fix simple cases**: If the fix is a straightforward find-and-replace or small API change (e.g., `seed=` → `rng=`, updating an import path), fix it directly in a companion PR to `mesa-examples`.
3. **Open tracking issues for complex cases**: If updating an example requires significant rework (e.g., replacing `DataCollector` with `DataRecorder`, restructuring a model to use new spaces), open a specific, well-scoped issue on `mesa-examples` instead. Tag it with `mesa-4-migration`.

#### What counts as "simple" vs "complex"
- **Simple** (fix directly): Parameter renames, import path changes, method renames, removing a deprecated kwarg, updating a single API call.
- **Complex** (open issue): Rewriting data collection, restructuring model to use new space architecture, replacing `batch_run` with new experimentation API, anything requiring understanding the model's logic to update correctly.

When in doubt, open an issue. A well-described issue is more valuable than a rushed, potentially broken fix.

#### Tracking issue format
Each issue should include:
- Which Mesa PR caused the breakage
- Which example(s) are affected
- What needs to change (with as much specificity as possible)
- A `mesa-4-migration` label

We maintain a **single umbrella tracking issue** that links to all individual migration issues, giving an overview of progress.

### CI and Testing
#### Required: Smoke tests
Every example on `main` must pass a basic smoke test: the model instantiates, runs for a handful of steps, and exits without errors. This is tested in CI on both `mesa/mesa` (on every push) and `mesa-examples` itself.

#### Not required (but welcome)
- Batch run tests
- Visualization tests
- Output validation

The bar is intentionally low to keep maintenance manageable. Core examples in `mesa/mesa` carry the heavier testing burden.

#### CI integration with Mesa
The `mesa/mesa` CI runs mesa-examples smoke tests against the development branch. When a PR in `mesa/mesa` causes failures:
1. CI flags the failure.
2. The PR author follows the responsibility model above (fix simple cases, open issues for complex ones).
3. A Mesa 4 PR is **not blocked** by mesa-examples failures, but the breakage must be tracked.

### Community Engagement
#### Making migration tasks accessible
To make it realistic for community members to contribute:

- Each migration issue should be **self-contained**: one example, one clear change needed.
- Issues should include a **concrete description** of what to change, ideally with before/after code snippets or a reference to the relevant migration guide section.
- Tag issues as `good first issue` when the change is mechanical and doesn't require deep model understanding.
- In the issue template, link to the relevant [migration guide](https://mesa.readthedocs.io/latest/migration_guide.html) section.

#### Encouraging contributions
- Mention open migration tasks in release notes and community channels.
- Consider a GSoC sub-project or community sprint for batch migration.
- Acknowledge contributors in release notes.

### Example Lifecycle

#### During Mesa 4 development
1. `mesa-3.x` branch is created as a snapshot.
2. As Mesa 4 PRs land, examples on `main` are updated (simple) or have issues opened (complex).
3. Community helps work through migration issues.
4. Before Mesa 4.0 release, assess which examples have been updated and which haven't.

#### At Mesa 4.0 release
- All examples on `main` should ideally pass smoke tests with Mesa 4.0.
- Examples that couldn't be updated remain on `main` with a failing test and an open issue. They are candidates for removal if not fixed within a reasonable period after release (decision deferred, revisited after release).

#### Post-release
- New examples submitted to `mesa-examples` must work with the latest Mesa version.
- If an example breaks due to a future Mesa update and nobody fixes it within two minor releases, maintainers may remove it from `main` (with a note pointing to the last working commit or branch).

### Summary of Key Decisions

| Question | Decision |
|---|---|
| Who updates broken examples? | PR author fixes simple cases, opens issues for complex ones |
| How do we handle Mesa 3 compatibility? | Branch-based: `mesa-3.x` branch preserves Mesa 3 examples |
| What testing is required? | Smoke tests (model runs without errors) |
| What about examples that can't be updated? | Defer removal decisions; track with issues; revisit post-release |
| How do we involve the community? | Self-contained, well-described issues tagged `mesa-4-migration` and `good first issue` |
