from collections import deque
import heapq
from graph.models import Graph


def is_connected(g: Graph) -> tuple[bool, list[int]]:
    if not g.stations:
        return False, []
    start = next(iter(g.stations))
    visited = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for voisin, _ in g.adjacency[node]:
            if voisin not in visited:
                queue.append(voisin)
    non_atteints = [s for s in g.stations if s not in visited]
    return len(non_atteints) == 0, non_atteints


def kruskal(g: Graph) -> tuple[list[tuple[int, int, int]], int]:
    parent = {s: s for s in g.stations}
    rank = {s: 0 for s in g.stations}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True

    seen, edges = set(), []
    for na, voisins in g.adjacency.items():
        for nb, duree in voisins:
            key = (min(na, nb), max(na, nb))
            if key not in seen:
                seen.add(key)
                edges.append((duree, na, nb))
    edges.sort()

    acpm, poids_total = [], 0
    for duree, na, nb in edges:
        if union(na, nb):
            acpm.append((na, nb, duree))
            poids_total += duree
            if len(acpm) == len(g.stations) - 1:
                break
    return acpm, poids_total


def dijkstra_v3(g: Graph, start_id: int, end_id: int, departure_time: int) -> tuple[list[int], int, list[dict]]:
    transfer_adj: dict[int, list[tuple[int, int]]] = {}
    for (a, b), tf in g.transfers.items():
        transfer_adj.setdefault(a, []).append((b, tf))

    INF = float('inf')
    time_at = {s: INF for s in g.stations}
    prev: dict[int, tuple[int, int]] = {}
    time_at[start_id] = departure_time
    pq = [(departure_time, start_id)]

    while pq:
        t, u = heapq.heappop(pq)
        if t > time_at[u]:
            continue
        if u == end_id:
            break
        for v, dur in g.adjacency[u]:
            next_dep = g.next_departure(u, v, t)
            if next_dep is None:
                continue
            arr = next_dep + dur
            if arr < time_at[v]:
                time_at[v] = arr
                prev[v] = (u, next_dep)
                heapq.heappush(pq, (arr, v))
        for v, tf in transfer_adj.get(u, []):
            arr = t + tf
            if arr < time_at[v]:
                time_at[v] = arr
                prev[v] = (u, t)
                heapq.heappush(pq, (arr, v))

    if time_at[end_id] == INF:
        return [], -1, []

    path, details, cur = [], [], end_id
    while cur in prev:
        p, dep = prev[cur]
        path.append(cur)
        details.append({
            'from_name': g.stations[p].name,
            'to_name': g.stations[cur].name,
            'line': g.stations[p].line,
            'departure': dep,
            'arrival': time_at[cur],
            'wait': max(0, dep - time_at[p]) if time_at[p] != INF else 0,
        })
        cur = p
    path.append(start_id)
    path.reverse()
    details.reverse()
    return path, time_at[end_id], details
