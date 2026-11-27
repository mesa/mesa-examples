import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent


class WalkerAgent(ContinuousSpaceAgent):
    def __init__(
        self,
        model,
        space,
        position,
        destination,
        speed,
    ):
        super().__init__(space, model)
        self.model = model

        self.G = model.G_layer

        self.position = np.array(position)
        self.destination = np.array(destination)
        self.speed = speed

        self.direction = np.zeros(2)
        self.reached = False
        self.step_time = 0

        self.update_grid_indices()

    def update_grid_indices(self):
        r = int(self.position[1] / self.G.cell_h)
        c = int(self.position[0] / self.G.cell_w)
        self.r = np.clip(r, 0, self.G.height - 1)
        self.c = np.clip(c, 0, self.G.width - 1)

    def calculate_deltaU(self):
        displacement = self.destination - self.position
        d_norm = np.linalg.norm(displacement)

        d_u = np.zeros(2) if d_norm < 0.05 else (displacement / d_norm)

        return d_u

    def calculate_deltaV(self):
        v = self.G.V

        i = self.r
        j = self.c
        i_d = min(i + 1, self.G.height - 1)
        i_u = max(i - 1, 0)
        j_r = min(j + 1, self.G.width - 1)
        j_l = max(j - 1, 0)

        gx = (v[i, j_r] - v[i, j_l]) / (2 * self.G.cell_w)
        gy = (v[i_d, j] - v[i_u, j]) / (2 * self.G.cell_h)

        d_v = np.array([gx, gy], dtype=float)

        return d_v

    def calculate_new_direction(self):
        grad_u = self.calculate_deltaU()
        grad_v = self.calculate_deltaV()

        v_norm = np.linalg.norm(grad_v)
        v_dir = grad_v / v_norm if v_norm > 0 else np.zeros(2)

        alignment = np.dot(
            grad_u, v_dir
        )  # Dot product: 1.0 = aligned, 0.0 = perpendicular, -1.0 = backward
        base_kappa = 4.0
        gamma = 0.2

        kappa = base_kappa * (1 + alignment) if alignment > -0.5 else 0

        effective_v = v_dir * min(v_norm, 1.0)
        new_dir = (
            grad_u + (effective_v * kappa) + (self.direction * gamma)
        )  # The Result: Destination + Trail + Inertia
        dir_norm = np.linalg.norm(new_dir)
        self.direction = np.zeros(2) if dir_norm < 0.05 else new_dir / dir_norm

    def position_update(self):
        noise = np.random.normal(loc=0, scale=0.1, size=2)
        new_pos = self.position + self.direction * self.speed + noise

        xmax = self.model.space_w
        ymax = self.model.space_h

        eps = 1e-3
        new_pos[0] = np.clip(new_pos[0], eps, xmax - eps)
        new_pos[1] = np.clip(new_pos[1], eps, ymax - eps)

        return new_pos

    def step(self):
        if np.linalg.norm(self.destination - self.position) < 1.0:
            self.reached = True
        else:
            self.position = self.position_update()

        self.step_time += 1

        self.update_grid_indices()


class StopsAgent(ContinuousSpaceAgent):
    def __init__(self, model, space, position):
        super().__init__(space, model)
        self.position = np.array(position)
        self.is_stop = True

    def step(self):
        pass
