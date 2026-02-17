import mesa
import numpy as np
from agent import StopsAgent, WalkerAgent
from mesa.agent import AgentSet
from mesa.experimental.continuous_space import ContinuousSpace
from mesa.space import PropertyLayer
from scipy.signal import convolve2d


class ActiveModel(mesa.Model):
    def __init__(
        self,
        stops=None,
        population_size=80,
        width=40,
        height=40,
        speed_mean=1.0,
        default_value=0,
        max_value=10,
        print_strength=5.0,
        trail_dies_in=2000,
        vision=4,
        resolution=2,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.space = ContinuousSpace(
            [[0, width], [0, height]],
            torus=False,
            random=self.random,
            n_agents=population_size,
        )

        self.space_w = width
        self.space_h = height

        if stops is None:
            self.stops = [
                (int(width * 0.1), int(height * 0.1)),  # Bottom-Left (approx)
                (int(width * 0.9), int(height * 0.1)),  # Bottom-Right (approx)
                (int(width * 0.5), int(height * 0.9)),  # Top-Middle
            ]
        else:
            self.stops = stops

        self.active_agents = AgentSet([])

        d, p = self.origin_destination(population_size)
        s = np.random.normal(loc=speed_mean, scale=0.1, size=population_size)

        self.G_layer = StepDeposit(
            self,
            width=width * resolution,
            height=height * resolution,
            default_value=default_value,
            max_value=max_value,
            print_strength=print_strength,
            trail_dies_in=trail_dies_in,
            vision=vision,
        )

        WalkerAgent.create_agents(
            model=self,
            space=self.space,
            n=population_size,
            destination=d,
            speed=s,
            position=p,
        )

        StopsAgent.create_agents(
            model=self, space=self.space, n=len(self.stops), position=self.stops
        )

    def origin_destination(self, k):
        s = list(self.stops)
        d = self.random.choices(s, k=k)
        p = []
        for i in range(k):
            s.remove(d[i])
            p.append(self.random.choice(s))
            s.append(d[i])
        p = np.array(p)
        if k == 1:
            return d[0], p[0]
        return d, p

    def step(self):
        zero_time = self.agents.select(
            lambda a: isinstance(a, WalkerAgent) and a.step_time == 0
        )

        if self.steps % 45 == 1:
            k = min(len(self.stops) + 2, len(zero_time))
            add_ag = self.random.choices(zero_time.to_list(), k=k)
            for add_a in add_ag:
                self.active_agents.add(add_a)

        self.active_agents.do("calculate_new_direction")
        self.active_agents.shuffle_do("step")

        agents_reached = self.active_agents.select(lambda a: a.reached)

        agent_to_remove = []
        for ag in agents_reached:
            if ag.step_time > 60:
                ag.step_time = 0
                agent_to_remove.append(ag)

            ag.destination, ag.position = self.origin_destination(1)
            ag.reached = False

        for remove_ag in agent_to_remove:
            self.active_agents.remove(remove_ag)

        self.G_layer.update()


class StepDeposit(PropertyLayer):
    def __init__(
        self,
        model,
        name="stepDeposit",
        width=1000,
        height=1000,
        default_value=0,
        max_value=1,
        print_strength=0.9,
        trail_dies_in=200,
        vision=20,
    ):
        super().__init__(name, width, height, default_value)

        self.model = model

        (_, xmax), (_, ymax) = self.model.space.dimensions
        self.cell_w = (xmax) / width
        self.cell_h = (ymax) / height

        self.sigma = vision

        self.V = np.zeros_like(self.data)

        stop_cells = []
        for x, y in self.model.stops:
            c = x // self.cell_w
            c = int(np.clip(c, 0, self.width - 1))
            r = y // self.cell_h
            r = int(np.clip(r, 0, self.height - 1))

            stop_cells.append([r, c])

        self.stop_cells = np.array(stop_cells)

        def create_diffuse_matrix():
            k_radius = int(3 * self.sigma)
            size = 1 + 2 * k_radius
            d = np.zeros((size, size), dtype=float)
            center = np.array([k_radius, k_radius])

            for r in range(size):
                for c in range(size):
                    dist = np.linalg.norm(np.array([r, c]) - center)
                    d[r, c] = np.exp(-dist / self.sigma)

            return d / d.sum()

        self.d = create_diffuse_matrix()

        self.max_value = max_value
        self.min_value = default_value
        self.print_strength = print_strength
        self.T = trail_dies_in

    def __getitem__(self, index):
        r, c = index
        return self.data[r, c]

    def updateV(self):
        self.V = convolve2d(self.data, self.d, mode="same")

    def decay(self):
        self.data = self.data - (self.data - self.min_value) / self.T

    def clean_stops(self):
        r_clear = self.sigma
        for stop_r, stop_c in self.stop_cells:
            r_min = max(0, stop_r - r_clear)
            r_max = min(self.height, stop_r + r_clear + 1)
            c_min = max(0, stop_c - r_clear)
            c_max = min(self.width, stop_c + r_clear + 1)

            self.data[r_min:r_max, c_min:c_max] = self.min_value

    def despositG(self):
        agents_pos_ind = np.array([[ag.r, ag.c] for ag in self.model.active_agents])
        if len(agents_pos_ind) == 0:
            return
        q = np.array([self.data[i, j] for i, j in agents_pos_ind])
        q = q / self.max_value
        q = (1 - q) * self.print_strength

        for ind, [i, j] in enumerate(agents_pos_ind):
            self.data[i, j] += q[ind]

        # self.clean_stops()

    def update(self):
        self.despositG()
        self.decay()

        self.updateV()


# parameters = {
#     'stops': [(5, 5), (35, 5), (20, 35)],
#     'population_size': 80,
#     'width': 40,
#     'height': 40,
#     'speed_mean': 1.0,

#     'default_value': 0,
#     'max_value': 10,

#     'print_strength': 5.0,
#     'trail_dies_in': 2000,

#     'vision': 4,
#     'resolution': 2,
#     'rng': None
# }
