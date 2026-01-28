import mesa
import heapq


class Dijkstra_JourneyAgent(mesa.Agent):
    """
    An agent that performs pathfinding using Dijkstra's algorithm.
    """

    def __init__(self, unique_id, model, start_pos, goal_pos):
        """
        Initialize the agent with a start position and a goal position.
        """
        super().__init__(unique_id, model)
        self.position = start_pos
        self.goal = goal_pos
        self.path = []  # To store the shortest path
        self.current_step = 0

    def step(self):
        """
        Move the agent along the computed path towards the goal.
        """
        if self.current_step < len(self.path):
            self.move_to(self.path[self.current_step])
            self.current_step += 1

    def move_to(self, new_position):
        """
        Move the agent to the specified position and update its grid location.
        """
        self.model.grid.move_agent(self, new_position)
        self.position = new_position

    def find_shortest_path(self, start, end):
        """
        Compute the shortest path using Dijkstra's algorithm.
        """
        width = self.model.grid.width
        height = self.model.grid.height

        def get_neighbors(position):
            x, y = position
            neighbors = [
                (x + dx, y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            ]
            neighbors = [
                (nx, ny) for nx, ny in neighbors if 0 <= nx < width and 0 <= ny < height
            ]
            return neighbors

        graph = {
            (x, y): get_neighbors((x, y)) for x in range(width) for y in range(height)
        }

        distances = {node: float("inf") for node in graph}
        previous_nodes = {node: None for node in graph}
        distances[start] = 0

        queue = [(0, start)]
        heapq.heapify(queue)

        while queue:
            current_distance, current_node = heapq.heappop(queue)

            if current_node == end:
                break

            for neighbor in graph[current_node]:
                distance = current_distance + 1  # All edges have weight 1
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(queue, (distance, neighbor))

        path = []
        step = end
        while step is not None:
            path.append(step)
            step = previous_nodes[step]
        path.reverse()

        return path

    def get_path(self):
        """
        Returns the computed path.
        """
        return self.path


class Dijkstra_JourneyModel(mesa.Model):
    """
    A model with agents that use Dijkstra's algorithm to find paths.
    """

    def __init__(self, num_agents, width, height):
        super().__init__()
        self.num_agents = num_agents
        self.schedule = mesa.time.RandomActivation(self)
        self.grid = mesa.space.MultiGrid(width, height, True)

        for i in range(self.num_agents):
            start_pos = (self.random.randrange(width), self.random.randrange(height))
            goal_pos = (self.random.randrange(width), self.random.randrange(height))
            agent = Dijkstra_JourneyAgent(i, self, start_pos, goal_pos)
            self.schedule.add(agent)
            self.grid.place_agent(agent, start_pos)
            agent.path = agent.find_shortest_path(
                start_pos, goal_pos
            )  # Compute the path

        self.datacollector = mesa.datacollection.DataCollector(
            {"num_agents": "num_agents"}
        )

    def step(self):
        """
        Advance the model by one step.
        """
        self.datacollector.collect(self)
        self.schedule.step()
