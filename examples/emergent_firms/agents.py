import mesa
import numpy as np


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

    @property
    def workers(self):
        """Return the AgentSet of member workers via the membership manager."""
        return self.model.meta_agents.members_of(self)

    @property
    def size(self):
        return len(self.workers)

    @property
    def total_effort(self):
        return sum(w.effort for w in self.workers)

    def compute_output(self):
        if self.size == 0:
            self.output = 0.0
            return

        # Production Function: O(E) = aE + bE^beta
        E = self.total_effort
        self.output = self.model.a * E + self.model.b * (E ** self.model.beta)

    def allocate_income(self):
        if self.size == 0:
            return

        income_per_worker = self.output / self.size
        for w in self.workers:
            w.income = income_per_worker
            w.utility = w.compute_utility(w.effort, income_per_worker)


class Worker(mesa.Agent):
    """
    Boundedly-rational individual optimizing its utility.
    """
    def __init__(self, model, theta):
        super().__init__(model)
        self.theta = theta
        self.effort = 0.0
        self.income = 0.0
        self.utility = 0.0
        self.friends = []

    @property
    def firm(self):
        """Return this worker's current firm via the membership manager, or None."""
        groups = self.model.meta_agents.groups_of(self)
        if len(groups) == 0:
            return None
        return list(groups)[0]

    def compute_utility(self, e, income):
        """Standardized Cobb-Douglas Utility U = I^theta * L^(1-theta) handling 0 limits safely."""
        if self.theta == 1.0:
            return income if e <= 1.0 else 0.0
        if self.theta == 0.0:
            return max(0.0, 1.0 - e)

        leisure = max(0.0, 1.0 - e)
        if income <= 0 or leisure <= 0:
            return 0.0

        return (income ** self.theta) * (leisure ** (1.0 - self.theta))

    def evaluate_firm(self, firm):
        """
        101-point line search for optimal effort in a given firm setting (as per Ch. 3.1)
        """
        if firm == self.firm:
            E_other = max(0.0, self.firm.total_effort - self.effort)
            N = self.firm.size
        elif firm is None:
            E_other = 0.0
            N = 1
        else:
            E_other = firm.total_effort
            N = firm.size + 1

        efforts = np.linspace(0.0, 1.0, 101)
        E_tot = E_other + efforts
        outputs = self.model.a * E_tot + self.model.b * (E_tot ** self.model.beta)
        incomes = np.maximum(outputs / N, 0.0)
        leisures = np.maximum(1.0 - efforts, 0.0)

        if self.theta == 1.0:
            utils = incomes
        elif self.theta == 0.0:
            utils = leisures
        else:
            with np.errstate(divide='ignore', invalid='ignore'):
                utils = (incomes ** self.theta) * (leisures ** (1.0 - self.theta))
            utils = np.nan_to_num(utils, nan=0.0)

        best_idx = np.argmax(utils)
        return efforts[best_idx], utils[best_idx], firm

    def step(self):
        options = []
        current_firm = self.firm

        # 1. Option: Evaluate current firm (Add trace epsilon to simulate minor inertia/loyalty against tie breaking)
        if current_firm:
            e_curr, u_curr, f_curr = self.evaluate_firm(current_firm)
            options.append((u_curr + 1e-9, e_curr, f_curr, "stay"))

        # 2. Option: Evaluate starting a brand new singleton firm
        e_new, u_new, _ = self.evaluate_firm(None)
        options.append((u_new, e_new, None, "new"))

        # 3. Option: Evaluate jumping to a friend's active firm
        evaluated_firms = {current_firm}
        for friend in self.friends:
            f_friend = friend.firm
            if f_friend and f_friend not in evaluated_firms:
                e_f, u_f, f_f = self.evaluate_firm(f_friend)
                options.append((u_f, e_f, f_f, "join"))
                evaluated_firms.add(f_friend)

        # Resolve Utility Maximization
        best_opt = max(options, key=lambda x: x[0])
        best_e = best_opt[1]
        best_f = best_opt[2]
        action = best_opt[3]

        # Apply the resolved movement decisions
        if action != "stay":
            if current_firm:
                self.model.meta_agents.remove_member(current_firm, self)
                if current_firm.size == 0:
                    self.model.meta_agents.dissolve(current_firm)

            if action == "new":
                self.model.meta_agents.create("Firm", [self], mesa_agent_type=Firm)
                self.model.new_firms_count += 1
            elif action == "join":
                self.model.meta_agents.add_member(best_f, self)
                # Expand social network: befriend a random coworker at the new firm
                if self.model.make_friends:
                    potential = [w for w in best_f.workers
                                 if w != self and w not in self.friends]
                    if potential:
                        self.friends.append(self.model.random.choice(potential))

        self.effort = best_e