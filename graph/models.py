from dataclasses import dataclass
from typing import Optional


@dataclass
class Station:
    id: int
    name: str
    line: str
    lat: float
    lon: float


class Graph:
    def __init__(self):
        self.stations: dict[int, Station] = {}
        self.adjacency: dict[int, list[tuple[int, int]]] = {}
        self.schedule: dict[tuple[int, int], list[int]] = {}
        self.transfers: dict[tuple[int, int], int] = {}

    def add_station(self, s: Station):
        self.stations[s.id] = s
        self.adjacency.setdefault(s.id, [])

    def add_edge(self, a: int, b: int, duration: int):
        self.adjacency[a].append((b, duration))
        self.adjacency[b].append((a, duration))

    def add_departure(self, stop_from: int, stop_to: int, time_sec: int):
        key = (stop_from, stop_to)
        self.schedule.setdefault(key, []).append(time_sec)

    def sort_schedules(self):
        for key in self.schedule:
            self.schedule[key].sort()

    def next_departure(self, stop_from: int, stop_to: int, current_time: int) -> Optional[int]:
        """Retourne l'heure du prochain départ >= current_time, ou None."""
        import bisect
        times = self.schedule.get((stop_from, stop_to), [])
        idx = bisect.bisect_left(times, current_time)
        return times[idx] if idx < len(times) else None
