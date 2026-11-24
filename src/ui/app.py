"""Submission dashboard. All values are simulation predictions, with no online dependencies."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import pandas as pd
import streamlit as st
import altair as alt
from src.pipeline.data_loader import DataLoader
from src.model.crowd_predictor import CrowdPredictor
from src.routing.router import SmartTransitRouter

st.set_page_config(page_title='Crowd-aware transport',layout='wide')
st.markdown('<style>'+Path(__file__).with_name('tokens.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
st.title('Smart Public Transport System')
st.subheader('Crowd-Aware Route Optimization')
st.info('SIMULATION: fictional transit lines inspired by Lucknow. Historical data is synthetically generated. Congestion is predicted, not live sensor data. No seating guarantee.')

@st.cache_resource
def load_system():
    return DataLoader.load_stations(), CrowdPredictor.load(), SmartTransitRouter()

try:
    stations,predictor,router = load_system()
except (ValueError,FileNotFoundError) as exc:
    st.error(str(exc))
    st.code('python -m src.model.train')
    st.stop()

ids=stations.station_id.tolist()
labels=dict(zip(stations.station_id,stations.name))
with st.sidebar:
    st.header('Plan a simulated trip')
    origin=st.selectbox('Origin',ids,index=1,format_func=lambda s:f'{s} - {labels[s]}')
    destination=st.selectbox('Destination',ids,index=2,format_func=lambda s:f'{s} - {labels[s]}')
    hour=st.slider('Departure hour',5,23,9)
    day=st.selectbox('Day of week',list(range(7)),index=1,format_func=lambda d:['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][d])
    weather=st.selectbox('Weather scenario',['Clear','Rain','Storm'])
    event=st.checkbox('Special-event scenario at all stations',value=False)
    comfort=st.slider('Crowd avoidance preference',0.0,5.0,2.0,.25)
    st.caption('0 disables crowd penalties. Larger preferences may increase travel time. Event input applies a hypothetical event to every station, broader than generator events.')
try:
    crowd=predictor.predict_network(ids,hour,day,weather,int(event))
    result=router.compare_routes(origin,destination,crowd,comfort)
    if result['status'] != 'SUCCESS':
        st.warning('No connected route is available for this trip.')
        st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()

base,smart=result['naive_route'],result['smart_route']
a=result['analytics']
st.subheader('Interactive simulated network')
st.caption('Blue: baseline. Green: recommendation. Gray: simulated network connections.')
coords={r.station_id:(r.longitude,r.latitude) for r in stations.itertuples()}
rows=[]
for i,(u,v,data) in enumerate(router.graph.edges(data=True)):
    for order,s in enumerate([u,v]):
        x,y=coords[s]
        rows.append(dict(longitude=x,latitude=y,order=order,segment=str(i),route='Network'))
for route,label in [(base,'Baseline'),(smart,'Recommended')]:
    for order,s in enumerate(route['stations']):
        x,y=coords[s]
        rows.append(dict(longitude=x,latitude=y,order=order,segment=label,route=label))
network=alt.Chart(pd.DataFrame(rows)).mark_line().encode(
    x=alt.X('longitude:Q',scale=alt.Scale(zero=False)),
    y=alt.Y('latitude:Q',scale=alt.Scale(zero=False)),
    detail='segment:N',order='order:Q',
    color=alt.Color('route:N',legend=alt.Legend(orient='bottom'),scale=alt.Scale(domain=['Network','Baseline','Recommended'],range=['#cbd5e1','#2563eb','#059669'])),
    size=alt.condition(alt.datum.route=='Network',alt.value(1),alt.value(4)))
points=stations.copy()
points['Predicted congestion']=points.station_id.map(crowd)
markers=alt.Chart(points).mark_circle(size=110).encode(
    x='longitude:Q',y='latitude:Q',color=alt.Color('Predicted congestion:Q',scale=alt.Scale(domain=[0,.35,.7,1],range=['#245c52','#6a857b','#ba7229','#9d3020']),legend=alt.Legend(title='Congestion',orient='bottom')),tooltip=['station_id','name',alt.Tooltip('Predicted congestion:Q',format='.3f')])
st.altair_chart((network+markers).resolve_scale(color='independent').properties(height=520).interactive(),use_container_width=True)
st.caption('Pan, zoom and hover station markers. This schematic uses illustrative coordinates and works offline once dependencies are installed.')

st.subheader('Compare itineraries')
col1,col2,col3=st.columns(3)
col1.metric('Signed exposure reduction',f"{a['crowd_reduction_percent']:+.2f}%")
col2.metric('Travel-time trade-off',f"{a['travel_time_delta_mins']:+.1f} min")
col3.metric('High-congestion stations avoided',str(a['bottlenecks_avoided']))
if not a['is_different_path']:
    st.success('Both methods recommend the same itinerary. No alternative has a lower weighted cost for this preference.')
else:
    st.write(f"The recommendation minimizes travel minutes plus an assumed crowd discomfort penalty. It changes average station exposure from {base['avg_congestion']:.3f} to {smart['avg_congestion']:.3f}, with {a['travel_time_delta_mins']:+.1f} minutes of extra travel. This optimizes a weighted sum, so average exposure need not improve in every case.")
for col,route,title in zip(st.columns(2),[base,smart],['Conventional baseline','Crowd-aware recommendation']):
    with col:
        st.subheader(title)
        st.write(' → '.join(route['station_names']))
        st.metric('Estimated duration',f"{route['total_time_mins']:.1f} min")
        st.caption(f"In vehicle: {route['in_vehicle_time_mins']:.1f} min; transfers: {route['transfer_time_mins']:.1f} min")
        st.write(f"Transfers: **{route['transfers']}** · Average congestion: **{route['avg_congestion']:.3f}** · Maximum: **{route['max_congestion']:.3f}** · High stations (≥0.70): **{len(route['bottlenecks'])}**")
        if route['segments']:
            st.dataframe(pd.DataFrame(route['segments'])[['from_station','to_station','line_name','base_time_mins','dest_crowd']],hide_index=True,use_container_width=True)

st.subheader('Predicted station congestion')
frame=pd.DataFrame({'Station':ids,'Predicted congestion':[crowd[s] for s in ids]})
st.bar_chart(frame.set_index('Station'))
st.dataframe(frame,hide_index=True,use_container_width=True)
st.caption(f"Model: {predictor.metrics['best_model_name']}. Held-out synthetic test MAE: {predictor.metrics['MAE']:.4f}. Exposure = arithmetic mean of station congestion including both endpoints; duration includes 4 minutes per line transfer. Predictions use one departure-time snapshot, not arrival-time forecasts.")
