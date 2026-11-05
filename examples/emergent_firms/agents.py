import mesa
import numpy as np

# Precomputed 101-point effort/leisure search grids shared across all evaluations
_EFFORT_GRID = np.linspace(0.0, 1.0, 101)
_LEISURE_GRID = np.maximum(1.0 - _EFFORT_GRID, 0.0)


class Firm(mesa.Agent):
    """
    Meta-agent representing a Firm. It aggregates the efforts of its
    Worker members and computes macro-production dynamics.

    Membership is tracked by the model's MetaAgents manager
    (model.meta_agents) rather than a local set.
    """
    def __init__(self, model, **kwargs):
        super().__init__(model)
        self.output = 0.0
        self.age = 0
        self._size: int | None = None
        self._total_effort: float | None = None
        self.free_riders = 0
        self.peak_size = 0
        self.peak_output = 0.0
        living = getattr(model, "_living_firms", None)
        if living is not None:
            living[self] = None

    def remove(self):
        living = getattr(self.model, "_living_firms", None)
        if living is not None:
            living.pop(self, None)
        super().remove()

    @property
    def workers(self):
        """Return the AgentSet of member workers via the membership manager."""
        return self.model.meta_agents.members_of(self)

    @property
    def size(self):
        if self._size is not None:
            return self._size
        return len(self.workers)

    @property
    def total_effort(self):
        if self._total_effort is not None:
            return self._total_effort
        return sum(w.effort for w in self.workers)

    def compute_output(self):
        n = self.size
        if n == 0:
            self.output = 0.0
            return

        # Production Function: O(E) = aE + bE^beta
        E = self.total_effort
        beta = self.model.beta
        e_beta = E * E if beta == 2.0 else (E ** beta)
        self.output = float(self.model.a * E + self.model.b * e_beta)
        if n > self.peak_size:
            self.peak_size = n
        if self.output > self.peak_output:
            self.peak_output = self.output

    def allocate_income(self):
        workers = self.workers
        n = len(workers)
        self._size = n
        if n == 0:
            self._total_effort = 0.0
            self.free_riders = 0
            return

        income_per_worker = self.output / n
        total_e = 0.0
        free_riders = 0
        for w in workers:
            e = w.effort
            total_e += e
            if e < 0.01:
                free_riders += 1
            w.income = income_per_worker
            w.utility = w.compute_utility(e, income_per_worker)
        # Re-anchor cached effort sum once per period to eliminate floating-point drift
        self._total_effort = total_e
        self.free_riders = free_riders


class Worker(mesa.Agent):
    """
    Boundedly-rational individual optimizing its utility.
    """
    def __init__(self, model, theta):
        super().__init__(model)
        self.theta = float(theta)
        self.effort = 0.0
        self.income = 0.0
        self.utility = 0.0
        self.friends = []
        self._friends_set = set()
        self._firm: Firm | None = None
        # Compact per-worker histories for O(1) Agent View lookup
        self.effort_history: list[float] = []
        self.income_history: list[float] = []
        # Precompute constant leisure^((1 - theta)) vector once per worker
        if 0.0 < self.theta < 1.0:
            self._leisure_pow = _LEISURE_GRID ** (1.0 - self.theta)
        else:
            self._leisure_pow = None

    @property
    def firm(self):
        """Return this worker's current firm via cached reference or the membership manager."""
        if self._firm is not None:
            return self._firm
        groups = self.model.meta_agents.groups_of(self)
        if len(groups) == 0:
            return None
        f = next(iter(groups))
        self._firm = f
        return f

    def compute_utility(self, e, income):
        """Standardized Cobb-Douglas Utility U = I^theta * L^(1-theta) handling 0 limits safely."""
        theta = self.theta
        if theta == 1.0:
            return income if e <= 1.0 else 0.0
        if theta == 0.0:
            return max(0.0, 1.0 - e)

        leisure = 1.0 - e
        if income <= 0.0 or leisure <= 0.0:
            return 0.0

        return (income ** theta) * (leisure ** (1.0 - theta))

    def evaluate_firm(self, firm):
        """
        101-point line search for optimal effort in a given firm setting (as per Ch. 3.1)
        """
        current = self.firm
        if current is not None and firm == current:
            E_other = max(0.0, current.total_effort - self.effort)
            N = current.size
        elif firm is None:
            E_other = 0.0
            N = 1
        else:
            E_other = firm.total_effort
            N = firm.size + 1

        E_tot = E_other + _EFFORT_GRID
        beta = self.model.beta
        e_beta = E_tot * E_tot if beta == 2.0 else (E_tot ** beta)
        incomes = (self.model.a * E_tot + self.model.b * e_beta) * (1.0 / N)

        theta = self.theta
        if theta == 1.0:
            utils = incomes
        elif theta == 0.0:
            utils = _LEISURE_GRID
        else:
            utils = (incomes ** theta) * self._leisure_pow

        best_idx = int(np.argmax(utils))
        return float(_EFFORT_GRID[best_idx]), float(utils[best_idx]), firm

    def step(self):
        options = []
        current_firm = self.firm
        old_e = self.effort
        firm_utils = {}

        # 1. Option: Evaluate current firm (Add trace epsilon to simulate minor inertia/loyalty against tie breaking)
        if current_firm:
            e_curr, u_curr, f_curr = self.evaluate_firm(current_firm)
            firm_utils[current_firm] = u_curr
            options.append((u_curr + 1e-9, e_curr, f_curr, "stay"))

        # 2. Option: Evaluate starting a brand new singleton firm
        e_new, u_new, _ = self.evaluate_firm(None)
        options.append((u_new, e_new, None, "new"))

        # 3. Option: Evaluate jumping to a friend's active firm
        for friend in self.friends:
            f_friend = friend.firm
            if f_friend and f_friend not in firm_utils:
                e_f, u_f, f_f = self.evaluate_firm(f_friend)
                firm_utils[f_friend] = u_f
                options.append((u_f, e_f, f_f, "join"))

        # Resolve Utility Maximization
        best_opt = max(options, key=lambda x: x[0])
        best_u = best_opt[0]
        best_e = best_opt[1]
        best_f = best_opt[2]
        action = best_opt[3]

        # Apply the resolved movement decisions and maintain cached firm aggregates in O(1)
        if action == "stay":
            self.effort = best_e
            if current_firm is not None and current_firm._total_effort is not None:
                current_firm._total_effort = max(0.0, current_firm._total_effort + (best_e - old_e))
        else:
            if current_firm is not None:
                self.model.meta_agents.remove_member(current_firm, self)
                self._firm = None
                new_size = (current_firm._size - 1) if current_firm._size is not None else len(current_firm.workers)
                current_firm._size = new_size
                if current_firm._total_effort is not None:
                    current_firm._total_effort = max(0.0, current_firm._total_effort - old_e)
                if new_size == 0:
                    if hasattr(self.model, "_dissolved_step_buf"):
                        self.model._dissolved_step_buf.append(current_firm.unique_id)
                    living = getattr(self.model, "_living_firms", None)
                    if living is not None:
                        living.pop(current_firm, None)
                    self.model.meta_agents.dissolve(current_firm)

            self.effort = best_e

            if action == "new":
                self.model.meta_agents.create("Firm", [self], mesa_agent_type=Firm)
                new_firm = next(iter(self.model.meta_agents.groups_of(self)))
                living = getattr(self.model, "_living_firms", None)
                if living is not None:
                    living[new_firm] = None
                self._firm = new_firm
                new_firm._size = 1
                new_firm._total_effort = best_e
                new_firm.peak_size = 1
                self.model.new_firms_count += 1
            elif action == "join":
                self.model.meta_agents.add_member(best_f, self)
                self._firm = best_f
                best_f._size = (best_f._size + 1) if best_f._size is not None else len(best_f.workers)
                if best_f._total_effort is not None:
                    best_f._total_effort += best_e
                if best_f._size > best_f.peak_size:
                    best_f.peak_size = best_f._size
                # Expand social network: befriend a random coworker at the new firm,
                # retaining highest-utility friends when at max_friends capacity
                if self.model.make_friends:
                    potential = [
                        w for w in best_f.workers
                        if w is not self and w not in self._friends_set
                    ]
                    if potential:
                        chosen = self.model.random.choice(potential)
                        max_friends = getattr(self.model, "max_friends", None)
                        if max_friends is None or len(self.friends) < max_friends:
                            self.friends.append(chosen)
                            self._friends_set.add(chosen)
                        elif self.friends:
                            worst_idx = min(
                                range(len(self.friends)),
                                key=lambda i: (
                                    firm_utils.get(self.friends[i].firm, -1.0),
                                    self.friends[i].effort,
                                ),
                            )
                            worst_friend = self.friends[worst_idx]
                            worst_score = (firm_utils.get(worst_friend.firm, -1.0), worst_friend.effort)
                            if worst_score < (best_u, chosen.effort):
                                self._friends_set.discard(worst_friend)
                                self.friends[worst_idx] = chosen
                                self._friends_set.add(chosen)