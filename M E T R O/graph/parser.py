import csv
from collections import defaultdict
from graph.models import Station, Graph

METRO_TYPE = '1'

def time_to_sec(t: str) -> int:
    h, m, s = t.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def load_gtfs(data_dir: str) -> Graph:
    g = Graph()

    metro_routes = {}
    with open(f"{data_dir}/routes.txt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row['route_type'].strip() == METRO_TYPE:
                metro_routes[row['route_id']] = row['route_short_name']

    metro_trips = {}
    with open(f"{data_dir}/trips.txt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row['route_id'] in metro_routes:
                metro_trips[row['trip_id']] = row['route_id']

    stops_info = {}
    stop_to_parent = {}
    with open(f"{data_dir}/stops.txt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stops_info[row['stop_id']] = {
                'name': row['stop_name'],
                'lat': float(row['stop_lat']),
                'lon': float(row['stop_lon']),
            }
            parent = row.get('parent_station', '').strip()
            stop_to_parent[row['stop_id']] = parent if parent else row['stop_id']

    trip_stops = defaultdict(list)
    with open(f"{data_dir}/stop_times.txt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row['trip_id'] in metro_trips:
                trip_stops[row['trip_id']].append({
                    'stop_id': row['stop_id'],
                    'seq': int(row['stop_sequence']),
                    'time': row['departure_time'],
                })

    node_counter = 0
    stop_id_to_node = {}
    edge_durations = defaultdict(list)

    def get_or_create(stop_id, line):
        nonlocal node_counter
        key = stop_to_parent.get(stop_id, stop_id)
        if key not in stop_id_to_node:
            info = stops_info.get(key, stops_info.get(stop_id, {}))
            stop_id_to_node[key] = node_counter
            g.add_station(Station(node_counter, info.get('name', key), line,
                                  info.get('lat', 0.0), info.get('lon', 0.0)))
            node_counter += 1
        stop_id_to_node[stop_id] = stop_id_to_node[key]
        return stop_id_to_node[key]

    for trip_id, route_id in metro_trips.items():
        line = metro_routes[route_id]
        stops = sorted(trip_stops[trip_id], key=lambda r: r['seq'])
        for i in range(len(stops) - 1):
            a, b = stops[i], stops[i + 1]
            t_a, t_b = time_to_sec(a['time']), time_to_sec(b['time'])
            if t_b - t_a <= 0:
                continue
            na = get_or_create(a['stop_id'], line)
            nb = get_or_create(b['stop_id'], line)
            if na == nb:
                continue
            edge_durations[(na, nb)].append(t_b - t_a)
            g.add_departure(na, nb, t_a)

    added = set()
    for (na, nb), durations in edge_durations.items():
        if (na, nb) not in added and (nb, na) not in added:
            g.add_edge(na, nb, sorted(durations)[len(durations) // 2])
            added.add((na, nb))

    g.sort_schedules()

    with open(f"{data_dir}/transfers.txt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sa = stop_to_parent.get(row['from_stop_id'], row['from_stop_id'])
            sb = stop_to_parent.get(row['to_stop_id'], row['to_stop_id'])
            if sa in stop_id_to_node and sb in stop_id_to_node:
                na, nb = stop_id_to_node[sa], stop_id_to_node[sb]
                if na != nb:
                    g.transfers[(na, nb)] = int(row.get('min_transfer_time', 0))

    return g