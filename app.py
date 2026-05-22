import streamlit as st
import plotly.graph_objects as go
import os
from datetime import time as dtime
from graph.parser import load_gtfs
from graph.algorithms import is_connected, kruskal, dijkstra_v3

st.set_page_config(page_title="Metro Paris", layout="wide")
st.title("Metro Paris")

@st.cache_resource(show_spinner="Chargement du graphe...")
def load_graph():
    base = os.path.dirname(os.path.abspath(__file__))
    return load_gtfs(os.path.join(base, "GTFS"))

g = load_graph()

name_to_id = {}
for sid, s in g.stations.items():
    if s.name not in name_to_id:
        name_to_id[s.name] = sid
station_names = sorted(name_to_id.keys())

LINE_COLORS = {
    '1':'#FFCE00','2':'#0064B0','3':'#9F9825','3B':'#98D4E2',
    '4':'#C04191','5':'#F28E42','6':'#83C491','7':'#F3A4BA',
    '7B':'#83C491','8':'#CEADD2','9':'#D5C900','10':'#C9910D',
    '11':'#8D5E2A','12':'#00814F','13':'#98D4E2','14':'#662483',
}

def line_color(line):
    return LINE_COLORS.get(str(line).upper().replace('M', ''), '#888888')

def sec_to_hhmm(s):
    s = int(s) % 86400
    return f"{s // 3600:02d}h{(s % 3600) // 60:02d}"

def build_map(g, highlight_path=None, highlight_acpm=None, acpm_steps=None):
    fig = go.Figure()

    line_data = {}
    seen = set()
    for na, voisins in g.adjacency.items():
        for nb, _ in voisins:
            key = (min(na, nb), max(na, nb))
            if key in seen:
                continue
            seen.add(key)
            sa, sb = g.stations[na], g.stations[nb]
            lk = sa.line
            if lk not in line_data:
                line_data[lk] = {'lats': [], 'lons': []}
            line_data[lk]['lats'].extend([sa.lat, sb.lat, None])
            line_data[lk]['lons'].extend([sa.lon, sb.lon, None])

    for line, data in line_data.items():
        fig.add_trace(go.Scattermapbox(
            lat=data['lats'], lon=data['lons'], mode='lines',
            line=dict(width=2, color=line_color(line)),
            hoverinfo='none', showlegend=False,
        ))

    if highlight_acpm:
        lats, lons = [], []
        for na, nb, _ in (highlight_acpm[:acpm_steps] if acpm_steps else highlight_acpm):
            sa, sb = g.stations[na], g.stations[nb]
            lats.extend([sa.lat, sb.lat, None])
            lons.extend([sa.lon, sb.lon, None])
        fig.add_trace(go.Scattermapbox(
            lat=lats, lon=lons, mode='lines',
            line=dict(width=4, color='#FF3333'),
            hoverinfo='none', showlegend=False,
        ))

    if highlight_path and len(highlight_path) > 1:
        lats, lons = [], []
        for i in range(len(highlight_path) - 1):
            sa, sb = g.stations[highlight_path[i]], g.stations[highlight_path[i + 1]]
            lats.extend([sa.lat, sb.lat, None])
            lons.extend([sa.lon, sb.lon, None])
        fig.add_trace(go.Scattermapbox(
            lat=lats, lon=lons, mode='lines',
            line=dict(width=5, color='#00DD88'),
            hoverinfo='none', showlegend=False,
        ))

    path_set = set(highlight_path) if highlight_path else set()
    fig.add_trace(go.Scattermapbox(
        lat=[s.lat for s in g.stations.values()],
        lon=[s.lon for s in g.stations.values()],
        mode='markers',
        marker=dict(
            size=[10 if sid in path_set else 7 for sid in g.stations],
            color=['#00DD88' if sid in path_set else line_color(g.stations[sid].line) for sid in g.stations],
        ),
        text=[f"{s.name} — L{s.line}" for s in g.stations.values()],
        hoverinfo='text', showlegend=False,
    ))

    fig.update_layout(
        mapbox=dict(style='open-street-map', center=dict(lat=48.8566, lon=2.3522), zoom=11),
        margin=dict(l=0, r=0, t=0, b=0), height=560,
    )
    return fig


tab1, tab2, tab3, tab4 = st.tabs(["Reseau", "Itineraire", "ACPM", "Connexite"])

with tab1:
    st.plotly_chart(build_map(g), use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    depart_name = col1.selectbox("Départ", station_names)
    arrivee_name = col2.selectbox("Arrivée", station_names, index=min(10, len(station_names) - 1))
    heure = st.time_input("Heure de départ", value=dtime(8, 0))

    if st.button("Calculer", type="primary"):
        start_id, end_id = name_to_id[depart_name], name_to_id[arrivee_name]
        if start_id == end_id:
            st.warning("Départ et arrivée identiques.")
        else:
            with st.spinner("Calcul..."):
                dep_sec = heure.hour * 3600 + heure.minute * 60
                path, arrival, details = dijkstra_v3(g, start_id, end_id, dep_sec)
            if not path:
                st.error("Aucun itinéraire trouvé.")
            else:
                total = arrival - dep_sec
                st.success(f"Arrivée : **{sec_to_hhmm(arrival)}** — Durée : **{total // 60} min**")
                for d in details:
                    wait_str = f" *(attente {d['wait'] // 60} min)*" if d['wait'] > 60 else ""
                    st.write(f"**L{d['line']}** {d['from_name']} `{sec_to_hhmm(d['departure'])}` -> {d['to_name']} `{sec_to_hhmm(d['arrival'])}`{wait_str}")
                st.plotly_chart(build_map(g, highlight_path=path), use_container_width=True)

with tab3:
    if st.button("Calculer l'ACPM", type="primary"):
        with st.spinner("Kruskal en cours..."):
            acpm, poids = kruskal(g)
        st.session_state['acpm'] = acpm
        st.session_state['acpm_poids'] = poids

    if 'acpm' in st.session_state:
        acpm, poids = st.session_state['acpm'], st.session_state['acpm_poids']
        st.success(f"**{len(acpm)} arêtes** — Poids total : **{poids // 60} min**")
        step = st.slider("Propagation", 1, len(acpm), len(acpm))
        st.plotly_chart(build_map(g, highlight_acpm=acpm, acpm_steps=step), use_container_width=True)

with tab4:
    if st.button("Verifier", type="primary"):
        connexe, non_atteints = is_connected(g)
        if connexe:
            st.success(f"Reseau connexe — {len(g.stations)} stations accessibles")
        else:
            st.error(f"Non connexe — {len(non_atteints)} stations isolees")
        st.plotly_chart(build_map(g), use_container_width=True)
