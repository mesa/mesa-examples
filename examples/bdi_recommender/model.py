import contextlib

try:
    from .agents import (
        ClinicAgent,
        DoctorAgent,
        GymAgent,
        NutritionCentreAgent,
        UserAgent,
    )
except ImportError:
    from agents import (
        ClinicAgent,
        DoctorAgent,
        GymAgent,
        NutritionCentreAgent,
        UserAgent,
    )
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid


class BDIRecommenderModel(Model):
    """BDI Recommender Agent Model.

    A model with one user (Bob) and one doctor demonstrating BDI architecture.
    The user has beliefs, desires, and computes goals. The doctor sends
    health recommendations that update the user's beliefs and intentions.

    Attributes:
        grid: OrthogonalMooreGrid for agent movement
        user: The UserAgent (Bob)
        doctor: The DoctorAgent
        datacollector: Collects agent beliefs and goals for analysis
    """

    def __init__(
        self,
        width: int = 40,
        height: int = 40,
        rng=None,
        user_desire_pa: float = 0.8,
        user_desire_wr: float = 0.8,
        doctor_proposal_tick: int = 3,
    ):
        """Initialize the BDI Recommender model.

        Args:
            width: Grid width
            height: Grid height
            rng: Random seed or generator
            user_desire_pa: User's desire for "Physical Activity" (0.0-1.0)
            user_desire_wr: User's desire for "Weight Reduction" (0.0-1.0)
            doctor_proposal_tick: Step at which doctor sends health proposal
        """
        if isinstance(rng, str):
            with contextlib.suppress(ValueError):
                rng = int(rng)
        super().__init__(rng=rng)

        # Create grid space
        self.grid = OrthogonalMooreGrid(
            (width, height), torus=False, random=self.random
        )

        # Create Doctor at center
        doctor_cell = self.grid[width // 2, height // 2]
        self.doctor = DoctorAgent(
            self,
            doctor_cell,
            initial_beliefs={"Not-pa": 1.0},
        )

        # Create Bob (User) at random position
        user_cell = self.grid.select_random_empty_cell()
        self.user = UserAgent(
            self,
            user_cell,
            initial_beliefs={"Not-eh": 0.4, "bs": 0.9},
            initial_desires={
                "pa": user_desire_pa,
                "wr": user_desire_wr,
                "eh": 0.9,
                "w": 0.75,
            },
        )

        # Create location agents at destination coordinates
        # These are the locations Bob visits based on recommendations
        self.gym = GymAgent(self, self.grid[21, 26])
        self.nutrition_centre = NutritionCentreAgent(self, self.grid[24, 22])
        self.clinic = ClinicAgent(self, self.grid[16, 19])

        # Establish relationship between user and doctor
        self.user.doctor = self.doctor

        # Data collection
        self.datacollector = DataCollector(
            agent_reporters={
                "beliefs": lambda a: dict(a.beliefs) if hasattr(a, "beliefs") else {},
                "trust": lambda a: a.trust if hasattr(a, "trust") else 0,
                "goals": lambda a: (
                    dict(a.goals) if hasattr(a, "goals") and callable(a.goals) else {}
                ),
            }
        )

        # Schedule the doctor to send a proposal at the specified tick
        self.schedule_event(self.doctor.send_proposal, at=float(doctor_proposal_tick))

        self.datacollector.collect(self)

    def step(self):
        """Execute one step of the model.

        Activates all agents and collects data.
        """
        self.agents.do("step")
        self.datacollector.collect(self)
