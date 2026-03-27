from collections import deque
from queue import PriorityQueue


class HoldingQueue:
    def __init__(self):
        self.items = PriorityQueue()
        self.arrival_order = 0
        self.orderingRule = "Emergency-first"

    def __len__(self):
        return self.size()

    def enqueue(self, aircraft, time: int) -> None:
        priority = 0 if aircraft.emergency else 1
        order = self.arrival_order
        self.arrival_order += 1

        self.items.put((priority, order, aircraft))

        aircraft.enteredHoldingAt = time
        aircraft.altitude = self.size() * 1000

    def enqueue_with_order(self, aircraft, time: int, order: int) -> None:
        priority = 0 if aircraft.emergency else 1
        self.items.put((priority, order, aircraft))

        aircraft.enteredHoldingAt = time

        # Critical fix: keep future orders unique
        if order >= self.arrival_order:
            self.arrival_order = order + 1

    def dequeue_with_order(self):
        if self.items.empty():
            return None
        return self.items.get()

    def dequeue(self):
        if self.items.empty():
            return None
        _, _, aircraft = self.items.get()
        return aircraft

    def peek(self):
        if self.items.empty():
            return None
        return self.items.queue[0][2]

    def size(self):
        return self.items.qsize()

    def is_empty(self):
        return self.items.empty()

    def to_list(self):
        return [t[2] for t in list(self.items.queue)]


class TakeOffQueue:
    def __init__(self):
        self.items = deque()
        self.orderingRule = "FIFO Only"

    def __len__(self):
        return self.size()

    def enqueue(self, aircraft, time: int) -> None:
        self.items.append(aircraft)
        aircraft.joinedTakeoffQueueAt = time

    def dequeue(self):
        if self.isEmpty():
            return None
        return self.items.popleft()

    def peek(self):
        if self.isEmpty():
            return None
        return self.items[0]

    def size(self):
        return len(self.items)

    def isEmpty(self):
        return not self.items

    def to_list(self):
        return list(self.items)
