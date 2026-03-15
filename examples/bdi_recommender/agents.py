"""BDI Agent classes for the Recommender example.

This module defines:
- BDIAgent: Mixin providing BDI (Belief-Desire-Intention) capabilities with reactive state
- UserAgent: Bob - a mobile agent seeking health recommendations
- DoctorAgent: A fixed agent providing medical advice

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mesa.discrete_space import Cell, FixedAgent, Grid2DMovingAgent
from mesa.experimental.mesa_signals import HasEmitters, Observable, computed_property

if TYPE_CHECKING:
    from model import BDIRecommenderModel


class BDIAgent(HasEmitters):
    """Mixin providing BDI (Belief-Desire-Intention) capabilities.

    Beliefs and trust are Observable, enabling reactive updates when changed.
    Goals are computed automatically from beliefs and desires.

    Attributes:
        beliefs: Observable dict mapping belief names to strength values
        desires: Dict mapping desire names to priority values
        trust: Observable trust level (0.0 to 1.0)
        intentions: List of (action_name, args) tuples to execute
        incoming_queue: Queue of received messages
    """

    beliefs = Observable()
    trust = Observable()

    def __init__(self, *args, **kwargs):
        """Initialize BDI agent with empty mental state."""
        super().__init__(*args, **kwargs)
        self.beliefs: dict[str, float] = {}
        self.desires: dict[str, float] = {}
        self.trust: float = 0.5
        self.intentions: list[tuple[str, tuple]] = []
        self.incoming_queue: list[dict[str, Any]] = []

    @computed_property
    def goals(self) -> dict[str, float]:
        """Compute goals from beliefs and desires.

        Goals are desires that are possible given current beliefs.
        A desire is blocked if there's a contradicting belief (Not-X blocks X).
        Returns the highest priority achievable desires.
        """
        return self.elect_goals()

    def elect_goals(self) -> dict[str, float]:
        """Elect goals from beliefs and desires using BDI logic.

        Implements the goal election algorithm from the NetLogo model:
        1. Find desires with highest priority
        2. Filter out desires blocked by conflicting beliefs
        3. Return remaining desires as goals
        """
        if not self.desires:
            return {}

        # Working copy of desires to filter down
        current_desires = self.desires.copy()

        while current_desires:
            # 1. Find maximum priority in the remaining set
            max_priority = max(current_desires.values())

            # 2. Get all desires with this max priority
            candidates = {k: v for k, v in current_desires.items() if v == max_priority}

            # 3. Filter out desires blocked by beliefs
            goals = {}
            for desire_name, priority in candidates.items():
                # Check for blocking belief (e.g., "Not-pa" blocks "pa")
                blocking_belief = f"Not-{desire_name}"
                if (
                    blocking_belief in self.beliefs
                    and self.beliefs[blocking_belief] > 0
                ):
                    continue  # Blocked by contradicting belief
                goals[desire_name] = priority

            # 4. If we found valid goals at this level, return them
            if goals:
                return goals

            # 5. If all candidates were blocked, remove them and LOOP to next priority level
            for key in candidates:
                del current_desires[key]

        return {}

    def add_intention(self, action: str, args: tuple = ()):
        """Add an intention to the agent's plan.

        Args:
            action: Name of the action method to execute
            args: Arguments to pass to the action
        """
        self.intentions.append((action, args))

    def clear_intentions(self):
        """Clear all intentions."""
        self.intentions.clear()

    def receive_message(self, message: dict[str, Any]):
        """Add a message to the incoming queue.

        Args:
            message: Dict with 'performative', 'sender', 'content' keys
        """
        self.incoming_queue.append(message)

    def get_message(self) -> dict[str, Any] | None:
        """Pop the next message from the queue.

        Returns:
            The next message dict, or None if queue is empty
        """
        if self.incoming_queue:
            return self.incoming_queue.pop(0)
        return None


class UserAgent(Grid2DMovingAgent, BDIAgent):
    """Bob - the user seeking health recommendations.

    A mobile BDI agent that:
    - Maintains beliefs about health conditions
    - Has desires for health outcomes
    - Computes goals from beliefs/desires
    - Receives recommendations from doctor
    - Moves to destinations based on recommendations
    """

    def __init__(
        self,
        model: BDIRecommenderModel,
        cell: Cell,
        initial_beliefs: dict[str, float] | None = None,
        initial_desires: dict[str, float] | None = None,
    ):
        """Initialize Bob with default beliefs and desires.

        Args:
            model: The BDIRecommenderModel instance
            cell: Starting cell position
            initial_beliefs: Optional dictionary of initial beliefs
            initial_desires: Optional dictionary of initial desires
        """
        super().__init__(model)
        self.cell = cell
        self.doctor: DoctorAgent | None = None

        # Initial beliefs (from NetLogo model or dynamic input)
        # Default: "Not-eh": Not experiencing health issues (0.4 confidence)
        # Default: "bs": Blood sugar concerns (0.9 confidence)
        self.beliefs = (
            initial_beliefs
            if initial_beliefs is not None
            else {"Not-eh": 0.4, "bs": 0.9}
        )

        # Initial desires (from NetLogo model or dynamic input)
        # Default: pa: physical activity, wr: weight reduction
        # Default: eh: exercise habit, w: wellness
        self.desires = (
            initial_desires
            if initial_desires is not None
            else {"pa": 0.8, "wr": 0.8, "eh": 0.9, "w": 0.75}
        )

        self.trust = 0.5
        self.destinations: list[tuple[int, int]] = []
        self.current_destination_index = 0

    def step(self):
        """Execute one step of Bob's behavior."""
        self.listen_to_messages()

        # If we have a destination to reach, move toward it
        if self.destinations and self.current_destination_index < len(
            self.destinations
        ):
            self.move_toward_destination()
        elif not self.intentions:
            # Compute goals and get recommendation if no current plan
            goals = self.goals
            if goals:
                self.get_recommendation(goals)

        self.execute_intentions()

    def listen_to_messages(self):
        """Process all incoming messages."""
        while msg := self.get_message():
            performative = msg.get("performative")
            if performative == "proposal":
                self.evaluate_proposal(msg)

    def evaluate_proposal(self, msg: dict[str, Any]):
        """Evaluate a proposal from another agent based on trust.

        Args:
            msg: Message dict with 'sender' and 'content' keys
        """
        sender = msg.get("sender")
        if sender and sender.trust > 0.5:
            # Accept proposal from trusted sender
            belief_update = msg.get("content", {})
            self.update_beliefs(belief_update)

            # Send acceptance
            response = {
                "performative": "accept",
                "sender": self,
                "receiver": sender,
                "content": belief_update,
            }
            sender.receive_message(response)
        # If not trusted, silently reject (no response)

    def update_beliefs(self, belief_update: dict[str, float]):
        """Update beliefs with new information.

        Args:
            belief_update: Dict of belief name -> new value
        """
        new_beliefs = self.beliefs.copy()

        for belief, value in belief_update.items():
            # Weight by sender's trust
            weighted_value = min(value, self.doctor.trust if self.doctor else 0.5)
            new_beliefs[belief] = weighted_value

        self.beliefs = new_beliefs

        # Recalculate goals and intentions
        self.clear_intentions()
        self.destinations.clear()
        self.current_destination_index = 0

        goals = self.goals
        if goals:
            self.get_recommendation(goals)

    def get_recommendation(self, goals: dict[str, float]):
        """Get health recommendation based on current goals.

        Based on NetLogo model's get-recommendation procedure.

        Args:
            goals: Current computed goals
        """
        # Check if physical activity (pa) and weight reduction (wr) are goals
        if "pa" in goals and "wr" in goals:
            # Recommend visiting multiple health locations
            self.destinations = [
                self.model.gym.cell.coordinate,
                self.model.nutrition_centre.cell.coordinate,
                self.model.clinic.cell.coordinate,
            ]
            self.add_intention("visit_locations", ())
        else:
            # Special diet recommendation - visit doctor
            if self.doctor and self.doctor.cell:
                coord = self.doctor.cell.coordinate
                self.destinations = [(coord[0], coord[1])]
                self.add_intention("visit_doctor", ())

        self.current_destination_index = 0

    def move_toward_destination(self):
        """Move one step toward the current destination."""
        if self.current_destination_index >= len(self.destinations):
            return

        dest = self.destinations[self.current_destination_index]
        current = self.cell.coordinate

        # move in direction of destination
        dx = 0 if dest[0] == current[0] else (1 if dest[0] > current[0] else -1)
        dy = 0 if dest[1] == current[1] else (1 if dest[1] > current[1] else -1)

        if dx != 0 or dy != 0:
            directions = {
                (-1, 0): "n",
                (1, 0): "s",
                (0, 1): "e",
                (0, -1): "w",
                (-1, 1): "ne",
                (-1, -1): "nw",
                (1, 1): "se",
                (1, -1): "sw",
            }
            if direction := directions.get((dx, dy)):
                self.move(direction)

        # Check if arrived at destination
        if self.cell.coordinate == dest:
            self.current_destination_index += 1

    def _get_location_name(self, coordinate: tuple[int, int]) -> str:
        """Get the human-readable name of a location at the given coordinate.

        Args:
            coordinate: (x, y) tuple

        Returns:
            Location name (e.g., "Doctor", "Gym")
        """

        cell = self.model.grid[coordinate]
        for agent in cell.agents:
            if hasattr(agent, "location_name"):
                return agent.location_name

        return f"Location {coordinate}"

    def execute_intentions(self):
        """Execute pending intentions."""

        if self.current_destination_index >= len(self.destinations) and self.intentions:
            # All destinations visited, clear intentions
            self.clear_intentions()


class DoctorAgent(FixedAgent, BDIAgent):
    """The doctor who provides health recommendations.

    A fixed BDI agent that:
    - Has high trust level
    - Sends proposals to connected users
    - Provides belief updates about health conditions
    """

    def __init__(
        self,
        model: BDIRecommenderModel,
        cell: Cell,
        initial_beliefs: dict[str, float] | None = None,
    ):
        """Initialize the doctor at a fixed position.

        Args:
            model: The BDIRecommenderModel instance
            cell: Fixed cell position
            initial_beliefs: Optional dictionary of initial beliefs
        """
        super().__init__(model)
        self.cell = cell

        # Doctor's beliefs (from NetLogo model or dynamic input)
        # Default: "Not-pa": 1.0 (Knows patient lacks physical activity)
        self.beliefs = (
            initial_beliefs if initial_beliefs is not None else {"Not-pa": 1.0}
        )
        self.desires = {}
        self.trust = 0.9  # High trust level
        self.proposal_sent = False

    location_name = "Doctor"

    def step(self):
        """Execute one step of doctor's behavior."""
        self.listen_to_messages()

    def listen_to_messages(self):
        """Process incoming messages."""
        while self.get_message():
            # Process accept messages (currently just consume them)
            pass

    def send_proposal(self):
        """Send a health proposal to the connected user."""
        # Find connected user (Bob)
        user = None
        for agent in self.model.agents:
            if isinstance(agent, UserAgent) and agent.doctor is self:
                user = agent
                break

        if user:
            # Send proposal with belief about physical activity
            belief_to_share = next(iter(self.beliefs.items()))
            proposal = {
                "performative": "proposal",
                "sender": self,
                "receiver": user,
                "content": {belief_to_share[0]: belief_to_share[1]},
            }
            user.receive_message(proposal)
            self.proposal_sent = True


class LocationAgent(FixedAgent):
    """Base class for fixed location agents (Gym, Clinic, etc.).

    These agents represent physical locations that Bob can visit.
    They are fixed and do not move or take actions.

    Attributes:
        location_type: String identifier for the type of location
        location_name: Human-readable name for the location
    """

    location_name: str = "Location"

    def __init__(self, model: BDIRecommenderModel, cell: Cell):
        """Initialize the location agent.

        Args:
            model: The BDIRecommenderModel instance
            cell: Fixed cell position
        """
        super().__init__(model)
        self.cell = cell


class GymAgent(LocationAgent):
    """Gym - a place for physical activity.

    Bob visits here for physical activity (pa) goals.
    """

    location_name = "Gym"


class NutritionCentreAgent(LocationAgent):
    """Nutrition Centre - a place for diet advice.

    Bob visits here for weight reduction (wr) goals.
    """

    location_name = "Nutrition Centre"


class ClinicAgent(LocationAgent):
    """Health Clinic - a place for medical checkups.

    Bob visits here for health-related consultations.
    """

    location_name = "Health Clinic"
