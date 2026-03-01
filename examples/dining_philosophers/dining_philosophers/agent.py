from enum import Enum, auto

from mesa.discrete_space import FixedAgent


class State(Enum):
    THINKING = auto()
    HUNGRY = auto()
    EATING = auto()


class ForkAgent(FixedAgent):
    def __init__(self, model):
        super().__init__(model)
        self.is_used = False
        self.owner = None

    @property
    def position(self):
        return self.cell.coordinate

    def __repr__(self):
        owner = None if self.owner is None else getattr(self.owner, "position", None)
        return f"Fork-{self.position}(used={self.is_used}, owner={owner})"


class PhilosopherAgent(FixedAgent):
    def __init__(self, model):
        super().__init__(model)
        self.state = State.THINKING
        self.total_eaten = 0
        self.ticks_since_state_change = 0
        self.total_wait_time = 0
        self.eating_count = 0

    @property
    def position(self):
        return self.cell.coordinate

    def _start_eating(self):
        self.total_wait_time += self.ticks_since_state_change
        self.eating_count += 1
        self.state = State.EATING
        self.ticks_since_state_change = 0

    def step(self):
        self.ticks_since_state_change += 1

        if (
            self.state == State.THINKING
            and self.random.random() < self.model.hungry_chance
        ):
            self.state = State.HUNGRY
            self.ticks_since_state_change = 0

        elif self.state == State.HUNGRY:
            self.try_to_eat()

        elif (
            self.state == State.EATING and self.random.random() < self.model.full_chance
        ):
            self.put_down_forks()
            self.state = State.THINKING
            self.total_eaten += 1
            self.ticks_since_state_change = 0

    def put_down_forks(self):
        my_forks = self._get_neighbor_forks()

        for fork in my_forks:
            if fork.owner == self:
                fork.is_used = False
                fork.owner = None

    def try_to_eat(self):
        current_strategy = self.model.strategy

        if current_strategy == "Naive":
            self.eat_strategy_naive()
        elif current_strategy == "Atomic":
            self.eat_strategy_atomic()
        elif current_strategy == "Cooperative":
            self.eat_strategy_cooperative()

    def eat_strategy_naive(self):
        my_forks = self._get_neighbor_forks()

        left_pos = (self.position - 1) % self.model.num_nodes
        right_pos = (self.position + 1) % self.model.num_nodes

        left_fork = next(f for f in my_forks if f.position == left_pos)
        right_fork = next(f for f in my_forks if f.position == right_pos)

        if left_fork.owner != self and not left_fork.is_used:
            left_fork.is_used = True
            left_fork.owner = self

        if left_fork.owner == self:
            if not right_fork.is_used:
                right_fork.is_used = True
                right_fork.owner = self
                self._start_eating()
            else:
                pass

    def eat_strategy_atomic(self):
        my_forks = self._get_neighbor_forks()

        if all(not fork.is_used for fork in my_forks):
            for fork in my_forks:
                fork.is_used = True
                fork.owner = self
            self._start_eating()

    def eat_strategy_cooperative(self):
        my_forks = self._get_neighbor_forks()

        # If any fork is used, we can't eat anyway
        if any(fork.is_used for fork in my_forks):
            return

        # Check neighbors
        left_p_pos = (self.position - 2) % self.model.num_nodes
        right_p_pos = (self.position + 2) % self.model.num_nodes

        neighbors_p = [
            p
            for p in self.model.agents_by_type[PhilosopherAgent]
            if p.position in (left_p_pos, right_p_pos)
        ]

        should_yield = False
        for p in neighbors_p:
            if p.state == State.HUNGRY:
                # Rule: Yield if neighbor has been waiting longer
                if p.ticks_since_state_change > self.ticks_since_state_change:
                    should_yield = True
                    break
                # Rule: Yield if wait time is same but neighbor has lower ID (break ties)
                elif p.ticks_since_state_change == self.ticks_since_state_change:
                    if p.position < self.position:
                        should_yield = True
                        break

        if should_yield:
            return

        # Eat if forks are free and no need to yield
        for fork in my_forks:
            fork.is_used = True
            fork.owner = self
        self._start_eating()

    def __repr__(self):
        return f"Phil-{self.position}({self.state.name})"

    def _get_neighbor_forks(self):
        return [
            agent
            for agent in self.cell.neighborhood.agents
            if isinstance(agent, ForkAgent)
        ]
