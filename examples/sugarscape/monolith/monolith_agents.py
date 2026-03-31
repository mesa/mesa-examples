import math

from mesa.discrete_space import CellAgent

# Thresholds (module level constants)
CRITICAL_THRESHOLD = 3
COMFORTABLE_THRESHOLD = 7
IMBALANCE_RATIO = 1.5


# Helper function
def get_distance(cell_1, cell_2):
    """
    Calculate the Euclidean distance between two positions

    used in trade.move()
    """

    x1, y1 = cell_1.coordinate
    x2, y2 = cell_2.coordinate
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx**2 + dy**2)


class Trader(CellAgent):
    """
    Trader:
    - has a metabolism of sugar and spice
    - harvest and trade sugar and spice to survive
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

    def get_trader(self, cell):
        """
        helper function used in self.trade_with_neighbors()
        """

        for agent in cell.agents:
            if isinstance(agent, Trader):
                return agent

    def calculate_welfare(self, sugar, spice):
        """
        helper function

        part 2 self.move()
        self.trade()
        """

        # calculate total resources
        m_total = self.metabolism_sugar + self.metabolism_spice
        # Cobb-Douglas functional form; starting on p. 97
        # on Growing Artificial Societies
        return sugar ** (self.metabolism_sugar / m_total) * spice ** (
            self.metabolism_spice / m_total
        )

    def is_starved(self):
        """
        Helper function for self.maybe_die()
        """

        return (self.sugar <= 0) or (self.spice <= 0)

    def calculate_MRS(self, sugar, spice):
        """
        Helper function for
          - self.trade()
          - self.maybe_self_spice()

        Determines what trader agent needs and can give up
        """

        return (spice / self.metabolism_spice) / (sugar / self.metabolism_sugar)

    def calculate_sell_spice_amount(self, price):
        """
        helper function for self.maybe_sell_spice() which is called from
        self.trade()
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
        used in self.maybe_sell_spice()

        exchanges sugar and spice between traders
        """

        self.sugar += sugar
        other.sugar -= sugar
        self.spice -= spice
        other.spice += spice

    def maybe_sell_spice(self, other, price, welfare_self, welfare_other):
        """
        helper function for self.trade()
        """

        sugar_exchanged, spice_exchanged = self.calculate_sell_spice_amount(
            price)

        # Assess new sugar and spice amount - what if change did occur
        self_sugar = self.sugar + sugar_exchanged
        other_sugar = other.sugar - sugar_exchanged
        self_spice = self.spice - spice_exchanged
        other_spice = other.spice + spice_exchanged

        # double check to ensure agents have resources

        if (
            (self_sugar <= 0)
            or (other_sugar <= 0)
            or (self_spice <= 0)
            or (other_spice <= 0)
        ):
            return False

        # trade criteria #1 - are both agents better off?
        both_agents_better_off = (
            welfare_self < self.calculate_welfare(self_sugar, self_spice)
        ) and (welfare_other < other.calculate_welfare(other_sugar, other_spice))

        # trade criteria #2 is their mrs crossing with potential trade
        mrs_not_crossing = self.calculate_MRS(
            self_sugar, self_spice
        ) > other.calculate_MRS(other_sugar, other_spice)

        if not (both_agents_better_off and mrs_not_crossing):
            return False

        # criteria met, execute trade
        self.sell_spice(other, sugar_exchanged, spice_exchanged)

        return True

    def trade(self, other):
        """
        helper function used in trade_with_neighbors()

        other is a trader agent object
        """

        # sanity check to verify code is working as expected
        assert self.sugar > 0
        assert self.spice > 0
        assert other.sugar > 0
        assert other.spice > 0

        # calculate marginal rate of substitution in Growing Artificial Societies p. 101
        mrs_self = self.calculate_MRS(self.sugar, self.spice)
        mrs_other = other.calculate_MRS(other.sugar, other.spice)

        # calculate each agents welfare
        welfare_self = self.calculate_welfare(self.sugar, self.spice)
        welfare_other = other.calculate_welfare(other.sugar, other.spice)

        if math.isclose(mrs_self, mrs_other):
            return

        # calculate price
        price = math.sqrt(mrs_self * mrs_other)

        if mrs_self > mrs_other:
            # self is a sugar buyer, spice seller
            sold = self.maybe_sell_spice(
                other, price, welfare_self, welfare_other)
            # no trade - criteria not met
            if not sold:
                return
        else:
            # self is a spice buyer, sugar seller
            sold = other.maybe_sell_spice(
                self, price, welfare_other, welfare_self)
            # no trade - criteria not met
            if not sold:
                return

        # Capture data
        self.prices.append(price)
        self.trade_partners.append(other.unique_id)

        # continue trading
        self.trade(other)

    ######################################################################
    #                                                                    #
    #                      MAIN TRADE FUNCTIONS                          #
    #                                                                    #
    ######################################################################

    def move(self, mode="default", urgent_resource=None):
        """
        - Movement logic now branches on mode.
        - This is where the bulky step method creates issues and gets ugly -
        - Every drive needs different cell scoring, all stuffed into one method
        """

        # 1. identify all possible moves

        neighboring_cells = [
            cell
            for cell in self.cell.get_neighborhood(self.vision, include_center=True)
            if cell.is_empty
        ]

        if not neighboring_cells:
            # all neighboring cells are occupied
            return

        # 2. Score cells differently depending on mode

        if mode == "survive":
            # Pure greedy: only care about the critical resource.
            if urgent_resource == "sugar":
                scores = [cell.sugar for cell in neighboring_cells]
            else:
                scores = [cell.spice for cell in neighboring_cells]

        elif mode == "gather_sugar":
            # Two-pass: first filter to cells with the most sugar,
            # then rank those by welfare as the tiebreaker.
            max_sugar = max(cell.sugar for cell in neighboring_cells)
            neighboring_cells = [
                cell for cell in neighboring_cells if cell.sugar == max_sugar
            ]
            scores = [
                self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                for cell in neighboring_cells
            ]

        elif mode == "gather_spice":
            # Same two-pass logic used in gather sugar.
            max_spice = max(cell.spice for cell in neighboring_cells)
            neighboring_cells = [
                cell for cell in neighboring_cells if cell.spice == max_spice
            ]
            scores = [
                self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                for cell in neighboring_cells
            ]

        elif mode == "seek_trade":
            """
            - Agent is comfortable but imbalanced
            - it wants to find traders who have the opposite imbalance
            - Score each cell by: base welfare + count of complementary
              traders reachable from that cell within vision.
            """
            sugar_ticks = self.sugar / self.metabolism_sugar
            spice_ticks = self.spice / self.metabolism_spice
            need_sugar = spice_ticks > sugar_ticks
            need_spice = sugar_ticks > spice_ticks

            scores = []
            for cell in neighboring_cells:
                base = self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                # Count traders reachable from this cell who have complementary surplus
                complementary_count = 0
                for agent in cell.get_neighborhood(radius=self.vision).agents:
                    if not isinstance(agent, Trader) or agent is self:
                        continue
                    other_sugar_t = agent.sugar / agent.metabolism_sugar
                    other_spice_t = agent.spice / agent.metabolism_spice
                    # I need sugar and and they have more sugar than spice
                    if (need_sugar and other_sugar_t > other_spice_t) or (
                        need_spice and other_spice_t > other_sugar_t
                    ):
                        complementary_count += 1

                # Each complementary trader adds the base welfare as bonus
                # So a cell near 2 good partners scores 3x a cell near none
                # Makes it proportional
                scores.append(base * (1 + complementary_count))

        else:
            # Default: original welfare-maximising behaviour
            scores = [
                self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                for cell in neighboring_cells
            ]

        # 3. Select best cell

        max_score = max(scores)
        candidates = [
            cell
            for cell, score in zip(neighboring_cells, scores)
            if math.isclose(score, max_score)
        ]

        min_dist = min(get_distance(self.cell, cell) for cell in candidates)

        final_candidates = [
            cell
            for cell in candidates
            if math.isclose(get_distance(self.cell, cell), min_dist, rel_tol=1e-02)
        ]

        # random choice tiebreaker
        self.cell = self.random.choice(final_candidates)

    def eat(self):
        self.sugar += self.cell.sugar
        self.cell.sugar = 0
        self.sugar -= self.metabolism_sugar

        self.spice += self.cell.spice
        self.cell.spice = 0
        self.spice -= self.metabolism_spice

    def maybe_die(self):
        """
        Function to remove Traders who have consumed all their sugar or spice
        """

        if self.is_starved():
            self.remove()

    def step(self):
        """
        MONOLITH STEP: All drive logic crammed into one method.

        Working, but look at what happens:
        - Adding a new drive means adding another elif branch here AND in move()
        - Changing how one drive affects trading means editing deep in this method
        - The interaction between urgency calculation and movement is implicit
        - Duplicated patterns across branches (eat + maybe_die in every path)
        """

        self.prices = []
        self.trade_partners = []

        # Compute urgency (ticks of reserves remaining)
        sugar_ticks = self.sugar / self.metabolism_sugar
        spice_ticks = self.spice / self.metabolism_spice

        # SURVIVAL: either resource is critically low
        if sugar_ticks < CRITICAL_THRESHOLD or spice_ticks < CRITICAL_THRESHOLD:
            self.active_drive = "survive"
            if sugar_ticks < spice_ticks:
                self.move(mode="survive", urgent_resource="sugar")
            else:
                self.move(mode="survive", urgent_resource="spice")
            self.eat()
            # No trading - survival is all that matters
            self.maybe_die()
            return

        # SEEK TRADE: both resources comfortable, but imbalanced
        if (
            sugar_ticks > COMFORTABLE_THRESHOLD
            and spice_ticks > COMFORTABLE_THRESHOLD
            and (
                sugar_ticks / spice_ticks > IMBALANCE_RATIO
                or spice_ticks / sugar_ticks > IMBALANCE_RATIO
            )
        ):
            self.active_drive = "seek_trade"
            self.move(mode="seek_trade")
            self.eat()
            self.maybe_die()
            return

        # GATHER SUGAR: sugar is the more urgent resource
        if sugar_ticks < spice_ticks:
            self.active_drive = "gather_sugar"
            self.move(mode="gather_sugar")
            self.eat()
            self.maybe_die()
            return

        # GATHER SPICE: spice is the more urgent resource
        if spice_ticks < sugar_ticks:
            self.active_drive = "gather_spice"
            self.move(mode="gather_spice")
            self.eat()
            self.maybe_die()
            return

        # BALANCED: resources roughly equal, so use default movement
        self.active_drive = "default"
        self.move(mode="default")
        self.eat()
        self.maybe_die()
        return

    def trade_with_neighbors(self):
        """
        Function for trader agents to decide who to trade with
        Now drive aware: survival drive skips trading entirely.
        This check is awkward here though since the drive was determined in step(),
        we're coupling two methods via instance state set in a completely different place.

        Three steps when trading.
        1- identify neighbors who can trade
        2- trade (2 sessions)
        3- collect data
        """
        # iterate through traders in neighboring cells and trade
        if self.active_drive == "survive":
            return

        for a in self.cell.get_neighborhood(radius=self.vision).agents:
            self.trade(a)

        return
