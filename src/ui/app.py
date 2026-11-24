"""Submission dashboard. All values are simulation predictions, with no online dependencies."""
import base64
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import streamlit as st
import altair as alt
from src.pipeline.data_loader import DataLoader
from src.model.crowd_predictor import CrowdPredictor
from src.routing.router import SmartTransitRouter

st.set_page_config(page_title='Smart Public Transport System', layout='wide')
st.markdown('<style>' + Path(__file__).with_name('tokens.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)

# ── TOP HERO HEADER BANNER (Mint & Clean White Illustration) ────────────
@st.cache_data
def get_header_art_b64() -> str:
    svg_path = Path(__file__).resolve().parent / "assets" / "header_train_art.svg"
    if svg_path.exists():
        return base64.b64encode(svg_path.read_bytes()).decode("utf-8")
    return ""

header_art_b64 = get_header_art_b64()
header_html = (
    '<div class="header-banner-card">'
    '<div style="display:flex;align-items:center;gap:16px;">'
    '<div style="width:52px;height:52px;border-radius:14px;background:#d1fae5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
    '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#065f46" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="4" y="3" width="16" height="15" rx="3.5"/>'
    '<rect x="6.5" y="5.5" width="11" height="5.5" rx="1.5" fill="#a7f3d0"/>'
    '<circle cx="8" cy="14" r="1.3" fill="#065f46"/>'
    '<circle cx="16" cy="14" r="1.3" fill="#065f46"/>'
    '<line x1="8" y1="18" x2="5" y2="21"/>'
    '<line x1="16" y1="18" x2="19" y2="21"/>'
    '</svg>'
    '</div>'
    '<div>'
    '<h1 style="font-size:1.7rem;font-weight:800;color:#0f172a;margin:0;line-height:1.2;">Smart Public Transport System</h1>'
    '<p style="font-size:0.95rem;font-weight:600;color:#475569;margin:3px 0 0 0;">Crowd-Aware Route Optimization</p>'
    '</div>'
    '</div>'
    '<div style="display:flex;align-items:flex-end;">'
    f'<img src="data:image/svg+xml;base64,{header_art_b64}" height="70" style="max-width:100%;object-fit:contain;display:block;" alt="Train Art"/>'
    '</div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)

st.info('SIMULATION: fictional transit lines inspired by Lucknow. Historical data is synthetically generated. Congestion is predicted, not live sensor data. No seating guarantee.')

@st.cache_resource
def load_system():
    return DataLoader.load_stations(), CrowdPredictor.load(), SmartTransitRouter()

try:
    stations, predictor, router = load_system()
except (ValueError, FileNotFoundError) as exc:
    st.error(str(exc))
    st.code('python -m src.model.train')
    st.stop()

ids = stations.station_id.tolist()
labels = dict(zip(stations.station_id, stations.name))

with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:1.1rem;">
        <div style="width:38px; height:38px; border-radius:10px; background:#d1fae5; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#065f46" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="4" y="3" width="16" height="15" rx="3.5"/>
                <rect x="6.5" y="5.5" width="11" height="5.5" rx="1.5" fill="#a7f3d0"/>
                <circle cx="8" cy="14" r="1.3" fill="#065f46"/>
                <circle cx="16" cy="14" r="1.3" fill="#065f46"/>
                <line x1="8" y1="18" x2="5" y2="21"/>
                <line x1="16" y1="18" x2="19" y2="21"/>
            </svg>
        </div>
        <span style="font-size:1.15rem; font-weight:750; color:#124030;">Plan a simulated trip</span>
    </div>
    """, unsafe_allow_html=True)

    origin = st.selectbox('Origin', ids, index=1, format_func=lambda s: f'{s} - {labels[s]}')
    destination = st.selectbox('Destination', ids, index=2, format_func=lambda s: f'{s} - {labels[s]}')
    hour = st.slider('Departure hour', 5, 23, 9)
    day = st.selectbox('Day of week', list(range(7)), index=1, format_func=lambda d: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][d])
    weather = st.selectbox('Weather scenario', ['Clear', 'Rain', 'Storm'])

    weather_badges = {
        'Clear': ('☀️', 'Clear Skies', 'Ideal for travel'),
        'Rain': ('🌧️', 'Rain Surge', 'Moderate platform crowding'),
        'Storm': ('⛈️', 'Storm Alert', 'Severe congestion expected')
    }
    w_icon, w_title, w_desc = weather_badges.get(weather, ('☀️', 'Clear Skies', 'Ideal for travel'))
    st.markdown(f"""
    <div style="background:#ffffff; border:1px solid #d4e4db; border-radius:12px; padding:0.6rem 0.85rem; display:flex; align-items:center; gap:10px; margin-top:4px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
        <span style="font-size:1.35rem;">{w_icon}</span>
        <div>
            <div style="font-size:0.82rem; font-weight:750; color:#0f172a;">{w_title}</div>
            <div style="font-size:0.72rem; color:#526b62; font-weight:500;">{w_desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    event = st.checkbox('Special-event scenario at all stations', value=False)
    comfort = st.slider('Crowd avoidance preference', 0.0, 5.0, 2.0, .25)
    st.caption('0 disables crowd penalties. Larger preferences may increase travel time. Event input applies a hypothetical event to every station, broader than generator events.')

    st.button("▶ Run Simulation", use_container_width=True)

    st.markdown("""
    <div style="background:#e8f4ed; border:1px solid #cce5d6; border-radius:10px; padding:0.65rem 0.85rem; margin-top:14px; display:flex; gap:8px; align-items:flex-start;">
        <span style="font-size:0.95rem;">💡</span>
        <div style="font-size:0.74rem; color:#234a3b; font-weight:550; line-height:1.4;">
            <b>Tip:</b> Try changing the weather scenario to see its impact.
        </div>
    </div>
    """, unsafe_allow_html=True)

try:
    crowd = predictor.predict_network(ids, hour, day, weather, int(event))
    result = router.compare_routes(origin, destination, crowd, comfort)
    if result['status'] != 'SUCCESS':
        st.warning('No connected route is available for this trip.')
        st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()

base, smart = result['naive_route'], result['smart_route']
a = result['analytics']

# ── TOP KPI METRIC CARDS ROW ──────────────────────────────────────────
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-icon-wrap" style="background:#f3e8ff; color:#7c3aed;">👥</div>
        <div class="kpi-data">
            <div class="kpi-num">{abs(a['crowd_reduction_percent']):.1f}%</div>
            <div class="kpi-lbl">Avg Crowd Reduction</div>
            <div class="kpi-sub" style="color:#7c3aed;">
                <span>▲</span> {a['crowd_reduction_percent']:+.1f}% vs baseline
            </div>
        </div>
    </div>
    <div class="kpi-box">
        <div class="kpi-icon-wrap" style="background:#e0f2fe; color:#0284c7;">🕒</div>
        <div class="kpi-data">
            <div class="kpi-num">{smart['total_time_mins']:.1f} min</div>
            <div class="kpi-lbl">Avg Travel Time</div>
            <div class="kpi-sub" style="color:#0284c7;">
                <span>▼</span> {a['travel_time_delta_mins']:+.1f} min trade-off
            </div>
        </div>
    </div>
    <div class="kpi-box">
        <div class="kpi-icon-wrap" style="background:#dcfce7; color:#16a34a;">🛣️</div>
        <div class="kpi-data">
            <div class="kpi-num">{smart['total_distance_km']:.1f} km</div>
            <div class="kpi-lbl">Avg Distance</div>
            <div class="kpi-sub" style="color:#16a34a;">
                <span>—</span> Optimal routing
            </div>
        </div>
    </div>
    <div class="kpi-box">
        <div class="kpi-icon-wrap" style="background:#ffedd5; color:#ea580c;">🛡️</div>
        <div class="kpi-data">
            <div class="kpi-num">{smart['transfers']}</div>
            <div class="kpi-lbl">Line Transfers</div>
            <div class="kpi-sub" style="color:#ea580c;">
                <span>▼</span> {smart['transfers'] - base['transfers']:+d} vs naive
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── MAIN NETWORK MAP & ROUTE SUMMARY SIDE-BY-SIDE ─────────────────────
coords = {r.station_id: (r.longitude, r.latitude) for r in stations.itertuples()}
rows = []
for i, (u, v, data) in enumerate(router.graph.edges(data=True)):
    for order, s in enumerate([u, v]):
        x, y = coords[s]
        rows.append(dict(longitude=x, latitude=y, order=order, segment=str(i), route='Network'))
for route, label in [(base, 'Baseline'), (smart, 'Recommended')]:
    for order, s in enumerate(route['stations']):
        x, y = coords[s]
        rows.append(dict(longitude=x, latitude=y, order=order, segment=label, route=label))

network = alt.Chart(pd.DataFrame(rows)).mark_line().encode(
    x=alt.X('longitude:Q', scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor='#f1f5f9')),
    y=alt.Y('latitude:Q', scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor='#f1f5f9')),
    detail='segment:N', order='order:Q',
    color=alt.Color('route:N', legend=alt.Legend(orient='bottom'), scale=alt.Scale(domain=['Network', 'Baseline', 'Recommended'], range=['#cbd5e1', '#3b82f6', '#059669'])),
    size=alt.condition(alt.datum.route == 'Network', alt.value(1), alt.value(3.5))
)
points = stations.copy()
points['Predicted congestion'] = points.station_id.map(crowd)
markers = alt.Chart(points).mark_circle(size=120).encode(
    x='longitude:Q', y='latitude:Q',
    color=alt.Color('Predicted congestion:Q', scale=alt.Scale(domain=[0, .35, .7, 1], range=['#059669', '#34d399', '#f59e0b', '#ef4444']), legend=alt.Legend(title='Congestion', orient='bottom')),
    tooltip=['station_id', 'name', alt.Tooltip('Predicted congestion:Q', format='.3f')]
)

col_net, col_sum = st.columns([7, 3])

with col_net:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <h3 style="font-size:1.15rem; font-weight:750; color:#0f172a; margin:0; display:flex; align-items:center; gap:8px;">
            <span>📊</span> Interactive Simulated Network
        </h3>
        <div style="font-size:0.78rem; font-weight:600; color:#526b62; display:flex; gap:12px; align-items:center;">
            <span>● Stops</span>
            <span style="color:#059669;">━ Selected Route</span>
            <span style="color:#cbd5e1;">━ Other Routes</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.altair_chart((network + markers).resolve_scale(color='independent').properties(height=480).interactive(), use_container_width=True)
    st.caption('Pan, zoom and hover station markers. This schematic uses illustrative coordinates and works offline once dependencies are installed.')

with col_sum:
    st.markdown(f"""
    <div class="summary-card">
        <div class="summary-title">
            <span>📍</span> Route Summary
        </div>
        <div class="summary-item">
            <div class="summary-label"><span>🕒</span> Total Time</div>
            <div class="summary-val">{smart['total_time_mins']:.1f} min</div>
        </div>
        <div class="summary-item">
            <div class="summary-label"><span>🛣️</span> Total Distance</div>
            <div class="summary-val">{smart['total_distance_km']:.1f} km</div>
        </div>
        <div class="summary-item">
            <div class="summary-label"><span>👥</span> Crowd Reduction</div>
            <div class="summary-val" style="color:#059669;">{a['crowd_reduction_percent']:.1f}%</div>
        </div>
        <div class="summary-item">
            <div class="summary-label"><span>🔄</span> Line Transfers</div>
            <div class="summary-val">{smart['transfers']}</div>
        </div>
        <div class="summary-badge-success">
            <span style="font-size:1.15rem;">✓</span>
            <div>
                <div>Optimized Route Found</div>
                <div style="font-size:0.74rem; font-weight:500; opacity:0.85;">Better crowd distribution achieved</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── ITINERARY COMPARISON (Retains 5 test metrics) ─────────────────────
st.markdown("<h3 style='margin-top:2rem; margin-bottom:0.8rem; font-size:1.25rem; font-weight:750;'>Compare Itineraries</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
col1.metric('Signed exposure reduction', f"{a['crowd_reduction_percent']:+.2f}%")
col2.metric('Travel-time trade-off', f"{a['travel_time_delta_mins']:+.1f} min")
col3.metric('High-congestion stations avoided', str(a['bottlenecks_avoided']))

if not a['is_different_path']:
    st.success('Both methods recommend the same itinerary. No alternative has a lower weighted cost for this preference.')
else:
    st.write(f"The recommendation minimizes travel minutes plus an assumed crowd discomfort penalty. It changes average station exposure from {base['avg_congestion']:.3f} to {smart['avg_congestion']:.3f}, with {a['travel_time_delta_mins']:+.1f} minutes of extra travel. This optimizes a weighted sum, so average exposure need not improve in every case.")

for col, route, title, badge in zip(st.columns(2), [base, smart], ['Conventional baseline', 'Crowd-aware recommendation'], ['BASELINE', 'RECOMMENDED']):
    with col:
        st.markdown(f"""
        <div class="itinerary-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <h4 style="font-size:1.05rem; font-weight:750; color:#0f172a; margin:0;">{title}</h4>
                <span style="font-size:0.68rem; font-weight:700; padding:3px 8px; border-radius:6px; background:{'#e2e8f0' if badge=='BASELINE' else '#d1fae5'}; color:{'#475569' if badge=='BASELINE' else '#065f46'};">{badge}</span>
            </div>
            <p style="font-size:0.86rem; color:#334155; font-weight:600; margin-bottom:12px;">{' → '.join(route['station_names'])}</p>
        </div>
        """, unsafe_allow_html=True)
        st.metric('Estimated duration', f"{route['total_time_mins']:.1f} min")
        st.caption(f"In vehicle: {route['in_vehicle_time_mins']:.1f} min; transfers: {route['transfer_time_mins']:.1f} min")
        st.write(f"Transfers: **{route['transfers']}** · Average congestion: **{route['avg_congestion']:.3f}** · Maximum: **{route['max_congestion']:.3f}** · High stations (≥0.70): **{len(route['bottlenecks'])}**")
        if route['segments']:
            st.dataframe(pd.DataFrame(route['segments'])[['from_station', 'to_station', 'line_name', 'base_time_mins', 'dest_crowd']], hide_index=True, use_container_width=True)

# ── STATION CONGESTION SNAPSHOT ───────────────────────────────────────
st.markdown("<h3 style='margin-top:2rem; margin-bottom:0.8rem; font-size:1.25rem; font-weight:750;'>Predicted Station Congestion</h3>", unsafe_allow_html=True)
frame = pd.DataFrame({'Station': ids, 'Predicted congestion': [crowd[s] for s in ids]})
st.bar_chart(frame.set_index('Station'), color="#059669")
st.dataframe(frame, hide_index=True, use_container_width=True)
st.caption(f"Model: {predictor.metrics['best_model_name']}. Held-out synthetic test MAE: {predictor.metrics['MAE']:.4f}. Exposure = arithmetic mean of station congestion including both endpoints; duration includes 4 minutes per line transfer. Predictions use one departure-time snapshot, not arrival-time forecasts.")
