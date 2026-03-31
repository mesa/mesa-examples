import math

from mesa.discrete_space import CellAgent

# Thresholds (module-level constants)
CRITICAL_THRESHOLD = 3
COMFORTABLE_THRESHOLD = 7
IMBALANCE_RATIO = 1.5


# Helper function
def get_distance(cell_1, cell_2):
    """
    Calculate the Euclidean distance between two positions.

    Used in Behaviour.choose_cell() for tiebreaking.
    """
    x1, y1 = cell_1.coordinate
    x2, y2 = cell_2.coordinate
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx**2 + dy**2)


######################################################################
#                                                                    #
#                        BEHAVIOUR CLASSES                           #
#                                                                    #
######################################################################


class Behaviour:
    """
    Base class for agent drives.

    Each behaviour defines:
      - name: string identifier used for data collection
      - score(): how urgent this behaviour is for the given agent
      - choose_cell(): which cell the agent should move to
      - act(): the full action sequence when this behaviour is selected

    Adding a new drive means subclassing Behaviour and appending
    it to the agent's self.behaviours list. No changes needed
    to the Trader class itself.
    """
    name = "default"

    def score(self, agent):
        raise NotImplementedError

    def choose_cell(self, agent):
        raise NotImplementedError

    def act(self, agent):
        raise NotImplementedError


class SurviveBehaviour(Behaviour):
    """
    Emergency drive: fires when either resource is critically low.

    Overrides normal behaviour — agent moves greedily toward the
    most urgent resource and skips trading entirely.
    """
    name = "survive"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Score is positive only when below critical threshold
        return max(0, CRITICAL_THRESHOLD - min(sugar_ticks, spice_ticks))

    def choose_cell(self, agent):
        """
        Pure greedy movement toward the critical resource.

        No welfare tiebreaker — when survival is at stake,
        the agent takes the richest cell for whichever
        resource is most urgent.
        """
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        urgent = "sugar" if sugar_ticks < spice_ticks else "spice"

        neighboring_cells = [
            cell
            for cell in agent.cell.get_neighborhood(
                agent.vision, include_center=True)
            if cell.is_empty
        ]

        if not neighboring_cells:
            return agent.cell

        # Score by the urgent resource only
        if urgent == "sugar":
            max_val = max(cell.sugar for cell in neighboring_cells)
            candidates = [
                cell for cell in neighboring_cells
                if cell.sugar == max_val
            ]
        else:
            max_val = max(cell.spice for cell in neighboring_cells)
            candidates = [
                cell for cell in neighboring_cells
                if cell.spice == max_val
            ]

        # Tiebreak: closest cell
        min_dist = min(get_distance(agent.cell, cell) for cell in candidates)
        final_candidates = [
            cell for cell in candidates
            if math.isclose(
                get_distance(agent.cell, cell), min_dist, rel_tol=1e-02)
        ]

        return agent.random.choice(final_candidates)

    def act(self, agent):
        agent.cell = self.choose_cell(agent)
        agent.eat()
        # No trading — survival is all that matters
        agent.maybe_die()


class GatherSugarBehaviour(Behaviour):
    """
    Resource drive: agent needs sugar more than spice.

    Two-pass cell selection: first filter to cells with the
    maximum sugar, then rank those by welfare as tiebreaker.
    Trades opportunistically if neighbours are available.
    """
    name = "gather_sugar"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Score is the deficit between spice ticks and sugar ticks
        return max(0, spice_ticks - sugar_ticks)

    def choose_cell(self, agent):
        """
        Two-pass: filter to cells with the most sugar,
        then rank those by welfare as tiebreaker.

        Tiebreaking chain: max sugar -> highest welfare -> closest -> random.
        """
        neighboring_cells = [
            cell
            for cell in agent.cell.get_neighborhood(
                agent.vision, include_center=True)
            if cell.is_empty
        ]

        if not neighboring_cells:
            return agent.cell

        # First pass: filter to cells with the most sugar
        max_sugar = max(cell.sugar for cell in neighboring_cells)
        sugar_cells = [
            cell for cell in neighboring_cells
            if cell.sugar == max_sugar
        ]

        # Second pass: rank by welfare as tiebreaker
        welfares = [
            agent.calculate_welfare(
                agent.sugar + cell.sugar,
                agent.spice + cell.spice,
            )
            for cell in sugar_cells
        ]

        max_welfare = max(welfares)
        candidates = [
            cell
            for cell, w in zip(sugar_cells, welfares)
            if math.isclose(w, max_welfare)
        ]

        # Tiebreak: closest cell
        min_dist = min(get_distance(agent.cell, cell) for cell in candidates)
        final_candidates = [
            cell for cell in candidates
            if math.isclose(
                get_distance(agent.cell, cell), min_dist, rel_tol=1e-02)
        ]

        return agent.random.choice(final_candidates)

    def act(self, agent):
        agent.cell = self.choose_cell(agent)
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


class GatherSpiceBehaviour(Behaviour):
    """
    Resource drive: agent needs spice more than sugar.

    Two-pass cell selection: first filter to cells with the
    maximum spice, then rank those by welfare as tiebreaker.
    Trades opportunistically if neighbours are available.
    """
    name = "gather_spice"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Score is the deficit between sugar ticks and spice ticks
        return max(0, sugar_ticks - spice_ticks)

    def choose_cell(self, agent):
        """
        Two-pass: filter to cells with the most spice,
        then rank those by welfare as tiebreaker.

        Tiebreaking chain: max spice -> highest welfare -> closest -> random.
        """
        neighboring_cells = [
            cell
            for cell in agent.cell.get_neighborhood(
                agent.vision, include_center=True)
            if cell.is_empty
        ]

        if not neighboring_cells:
            return agent.cell

        # First pass: filter to cells with the most spice
        max_spice = max(cell.spice for cell in neighboring_cells)
        spice_cells = [
            cell for cell in neighboring_cells
            if cell.spice == max_spice
        ]

        # Second pass: rank by welfare as tiebreaker
        welfares = [
            agent.calculate_welfare(
                agent.sugar + cell.sugar,
                agent.spice + cell.spice,
            )
            for cell in spice_cells
        ]

        max_welfare = max(welfares)
        candidates = [
            cell
            for cell, w in zip(spice_cells, welfares)
            if math.isclose(w, max_welfare)
        ]

        # Tiebreak: closest cell
        min_dist = min(get_distance(agent.cell, cell) for cell in candidates)
        final_candidates = [
            cell for cell in candidates
            if math.isclose(
                get_distance(agent.cell, cell), min_dist, rel_tol=1e-02)
        ]

        return agent.random.choice(final_candidates)

    def act(self, agent):
        agent.cell = self.choose_cell(agent)
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


class SeekTradeBehaviour(Behaviour):
    """
    Trade drive: agent is comfortable but has an imbalanced surplus.

    Only activates when both resources are above the comfortable
    threshold. Scores cells by base welfare weighted by the count
    of complementary traders reachable from that cell.

    This is the drive that directly addresses Axtell's friction —
    agents actively move toward beneficial trade partners rather
    than passively stumbling into them.
    """
    name = "seek_trade"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Only scores positive when both resources are comfortable
        if (sugar_ticks > COMFORTABLE_THRESHOLD
                and spice_ticks > COMFORTABLE_THRESHOLD):
            return max(sugar_ticks / spice_ticks, spice_ticks / sugar_ticks)
        return 0

    def choose_cell(self, agent):
        """
        Score cells by base welfare multiplied by count of
        complementary traders reachable from that cell.

        A cell near 2 good trade partners scores 3x a cell
        near none. This is proportional, not arbitrary.
        """
        neighboring_cells = [
            cell
            for cell in agent.cell.get_neighborhood(
                agent.vision, include_center=True)
            if cell.is_empty
        ]

        if not neighboring_cells:
            return agent.cell

        # Determine what we need based on imbalance
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        need_sugar = spice_ticks > sugar_ticks
        need_spice = sugar_ticks > spice_ticks

        scores = []
        for cell in neighboring_cells:
            base = agent.calculate_welfare(
                agent.sugar + cell.sugar,
                agent.spice + cell.spice,
            )
            # Count traders reachable from this cell who have
            # a complementary surplus
            complementary_count = 0
            for other in cell.get_neighborhood(radius=agent.vision).agents:
                if not isinstance(other, Trader) or other is agent:
                    continue
                other_sugar_t = other.sugar / other.metabolism_sugar
                other_spice_t = other.spice / other.metabolism_spice
                # I need sugar and they have more sugar than spice
                if need_sugar and other_sugar_t > other_spice_t:
                    complementary_count += 1
                # I need spice and they have more spice than sugar
                elif need_spice and other_spice_t > other_sugar_t:
                    complementary_count += 1

            # Proportional bonus: each complementary trader
            # multiplies the base welfare score
            scores.append(base * (1 + complementary_count))

        # Select best cell
        max_score = max(scores)
        candidates = [
            cell
            for cell, score in zip(neighboring_cells, scores)
            if math.isclose(score, max_score)
        ]

        # Tiebreak: closest cell
        min_dist = min(get_distance(agent.cell, cell) for cell in candidates)
        final_candidates = [
            cell for cell in candidates
            if math.isclose(
                get_distance(agent.cell, cell), min_dist, rel_tol=1e-02)
        ]

        return agent.random.choice(final_candidates)

    def act(self, agent):
        agent.cell = self.choose_cell(agent)
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


class DefaultBehaviour(Behaviour):
    """
    Fallback drive: resources are roughly balanced.

    Uses the original welfare-maximising movement from
    Epstein & Axtell. Always scores just above zero so
    it loses to any real drive.
    """
    name = "default"

    def score(self, agent):
        return 0.01

    def choose_cell(self, agent):
        """
        Original welfare-maximising cell selection.

        Identical to the movement logic in Mesa's built-in
        Sugarscape — pick the cell that maximises Cobb-Douglas
        welfare, tiebreak by distance, then random.
        """
        neighboring_cells = [
            cell
            for cell in agent.cell.get_neighborhood(
                agent.vision, include_center=True)
            if cell.is_empty
        ]

        if not neighboring_cells:
            return agent.cell

        welfares = [
            agent.calculate_welfare(
                agent.sugar + cell.sugar,
                agent.spice + cell.spice,
            )
            for cell in neighboring_cells
        ]

        max_welfare = max(welfares)
        candidates = [
            cell
            for cell, w in zip(neighboring_cells, welfares)
            if math.isclose(w, max_welfare)
        ]

        # Tiebreak: closest cell
        min_dist = min(get_distance(agent.cell, cell) for cell in candidates)
        final_candidates = [
            cell for cell in candidates
            if math.isclose(
                get_distance(agent.cell, cell), min_dist, rel_tol=1e-02)
        ]

        return agent.random.choice(final_candidates)

    def act(self, agent):
        agent.cell = self.choose_cell(agent)
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


######################################################################
#                                                                    #
#                          TRADER AGENT                              #
#                                                                    #
######################################################################


class Trader(CellAgent):
    """
    Trader agent with fully decoupled, behaviour-driven actions.

    Each tick, the behaviour with the highest score is selected.
    That behaviour controls the full action sequence: cell selection,
    eating, trading. The Trader class itself has no move() method —
    movement is owned entirely by the behaviours.

    Adding a new drive means writing one new Behaviour subclass
    and appending it to self.behaviours. No changes to the Trader
    class, model, or any other behaviour.
    """

    def __init__(
        self,
        model,
        cell,
        sugar=0,
        spice=0,
        metabolism_sugar=0,
        metabolism_spice=0,
        vision=0,
    ):
        super().__init__(model)
        self.cell = cell
        self.sugar = sugar
        self.spice = spice
        self.metabolism_sugar = metabolism_sugar
        self.metabolism_spice = metabolism_spice
        self.vision = vision
        self.prices = []
        self.trade_partners = []
        self.active_drive = None

        # Behaviours — extend by appending new Behaviour subclasses
        self.behaviours = [
            SurviveBehaviour(),
            GatherSugarBehaviour(),
            GatherSpiceBehaviour(),
            SeekTradeBehaviour(),
            DefaultBehaviour(),
        ]

    ######################################################################
    #                                                                    #
    #                        TRADE HELPERS                               #
    #                                                                    #
    ######################################################################

    def get_trader(self, cell):
        """Helper function used in self.trade_with_neighbors()"""
        for agent in cell.agents:
            if isinstance(agent, Trader):
                return agent

    def calculate_welfare(self, sugar, spice):
        """
        Cobb-Douglas welfare function.

        From Growing Artificial Societies p. 97.
        Used in Behaviour.choose_cell() for cell scoring
        and in trade() for evaluating whether a trade
        improves both agents' welfare.
        """
        m_total = self.metabolism_sugar + self.metabolism_spice
        return sugar ** (self.metabolism_sugar / m_total) * spice ** (
            self.metabolism_spice / m_total
        )

    def is_starved(self):
        """Helper function for self.maybe_die()"""
        return (self.sugar <= 0) or (self.spice <= 0)

    def calculate_MRS(self, sugar, spice):
        """
        Marginal Rate of Substitution.

        From Growing Artificial Societies p. 101.
        Determines what the trader needs and can give up.
        """
        return (spice / self.metabolism_spice) / (sugar / self.metabolism_sugar)

    def calculate_sell_spice_amount(self, price):
        """
        Helper function for self.maybe_sell_spice().

        Determines the quantities of sugar and spice to exchange
        at a given price.
        """
        if price >= 1:
            sugar = 1
            spice = int(price)
        else:
            sugar = int(1 / price)
            spice = 1
        return sugar, spice

    def sell_spice(self, other, sugar, spice):
        """
        Execute a spice-for-sugar exchange between two traders.

        Used in self.maybe_sell_spice().
        """
        self.sugar += sugar
        other.sugar -= sugar
        self.spice -= spice
        other.spice += spice

    def maybe_sell_spice(self, other, price, welfare_self, welfare_other):
        """
        Evaluate and potentially execute a spice sale.

        Checks two criteria before trading:
        1. Both agents must be better off after the trade
        2. MRS crossing condition must not be violated
        """
        sugar_exchanged, spice_exchanged = self.calculate_sell_spice_amount(
            price)

        # Assess hypothetical post-trade amounts
        self_sugar = self.sugar + sugar_exchanged
        other_sugar = other.sugar - sugar_exchanged
        self_spice = self.spice - spice_exchanged
        other_spice = other.spice + spice_exchanged

        # Ensure neither agent runs out of either resource
        if (
            (self_sugar <= 0)
            or (other_sugar <= 0)
            or (self_spice <= 0)
            or (other_spice <= 0)
        ):
            return False

        # Trade criteria #1 — are both agents better off?
        both_agents_better_off = (
            welfare_self < self.calculate_welfare(self_sugar, self_spice)
        ) and (welfare_other < other.calculate_welfare(other_sugar, other_spice))

        # Trade criteria #2 — MRS crossing condition
        mrs_not_crossing = self.calculate_MRS(
            self_sugar, self_spice
        ) > other.calculate_MRS(other_sugar, other_spice)

        if not (both_agents_better_off and mrs_not_crossing):
            return False

        # Criteria met, execute trade
        self.sell_spice(other, sugar_exchanged, spice_exchanged)
        return True

    def trade(self, other):
        """
        Bilateral trade between self and other.

        Computes MRS for both agents, determines price as the
        geometric mean, and executes the trade if beneficial.
        Recurses until no further beneficial trades are possible.
        """
        assert self.sugar > 0
        assert self.spice > 0
        assert other.sugar > 0
        assert other.spice > 0

        # Calculate marginal rate of substitution (p. 101)
        mrs_self = self.calculate_MRS(self.sugar, self.spice)
        mrs_other = other.calculate_MRS(other.sugar, other.spice)

        # Calculate each agent's welfare
        welfare_self = self.calculate_welfare(self.sugar, self.spice)
        welfare_other = other.calculate_welfare(other.sugar, other.spice)

        if math.isclose(mrs_self, mrs_other):
            return

        # Price is geometric mean of both MRS values
        price = math.sqrt(mrs_self * mrs_other)

        if mrs_self > mrs_other:
            # Self is a sugar buyer, spice seller
            sold = self.maybe_sell_spice(
                other, price, welfare_self, welfare_other)
        else:
            # Self is a spice buyer, sugar seller
            sold = other.maybe_sell_spice(
                self, price, welfare_other, welfare_self)

        if not sold:
            return

        # Capture data
        self.prices.append(price)
        self.trade_partners.append(other.unique_id)

        # Continue trading until no further benefit
        self.trade(other)

    ######################################################################
    #                                                                    #
    #                      MAIN AGENT FUNCTIONS                          #
    #                                                                    #
    ######################################################################

    def eat(self):
        """Harvest resources from current cell and pay metabolism costs."""
        self.sugar += self.cell.sugar
        self.cell.sugar = 0
        self.sugar -= self.metabolism_sugar

        self.spice += self.cell.spice
        self.cell.spice = 0
        self.spice -= self.metabolism_spice

    def maybe_die(self):
        """Remove trader if either sugar or spice is exhausted."""
        if self.is_starved():
            self.remove()

    def step(self):
        """
        Behaviour-driven step.

        The highest-scoring behaviour determines the full action
        sequence for this tick — cell selection, eating, and trading
        are all controlled by the selected behaviour's act() method.

        Compare to the monolith version where this logic is spread
        across step(), move(), and trade_with_neighbors() via string
        flags and if/elif chains.
        """
        self.prices = []
        self.trade_partners = []

        # Select the most urgent behaviour
        best = max(self.behaviours, key=lambda b: b.score(self))
        self.active_drive = best.name

        # Behaviour controls the full action sequence
        best.act(self)

    def trade_with_neighbors(self):
        """
        Trade with all traders within vision.

        Called by the active behaviour's act() method — not by the
        model. This means the behaviour controls whether trading
        happens at all (survive skips it) and when it happens
        relative to movement and eating.
        """
        for a in self.cell.get_neighborhood(radius=self.vision).agents:
            if isinstance(a, Trader):
                self.trade(a)
