import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd

st.set_page_config(page_title="Route Map", page_icon="🗺️", layout="wide")

if 'optimization_result' not in st.session_state or st.session_state.optimization_result is None:
    st.warning("⚠️ No optimization results found. Please run an optimization first.")
    if st.button("← Back to Home"):
        st.session_state.page = 'Home'
        st.switch_page("app.py")
    st.stop()

r = st.session_state.optimization_result

st.markdown("# 🗺️ Route Map")
st.markdown("### Interactive Multi-Modal Route Visualization")
st.markdown("---")

# ========== CITY COORDINATES ==========
city_coords = {
    'Delhi': [28.6139, 77.2090],
    'Mumbai': [19.0760, 72.8777],
    'Chennai': [13.0827, 80.2707],
    'Bengaluru': [12.9716, 77.5946],
    'Kolkata': [22.5726, 88.3639],
    'Hyderabad': [17.3850, 78.4867],
    'Nagpur': [21.1458, 79.0882],
    'Jogighopa': [26.2265, 90.5746],
    'Guwahati': [26.1445, 91.7362],
    'Kochi': [9.9312, 76.2673],
    'Goa': [15.2993, 74.1240],
    'Vizag': [17.6868, 83.2185],
    'Ahmedabad': [23.0225, 72.5714],
    'Pune': [18.5204, 73.8567],
    'Jaipur': [26.9124, 75.7873],
    'Lucknow': [26.8467, 80.9462],
    'Chandigarh': [30.7333, 76.7794],
    'Srinagar': [34.0837, 74.7973],
    'Thiruvananthapuram': [8.5241, 76.9366],
    'Bhubaneswar': [20.2961, 85.8245],
    'Patna': [25.5941, 85.1376],
    'Varanasi': [25.3176, 82.9739],
    'Surat': [21.1702, 72.8311],
    'Bhopal': [23.2599, 77.4126],
    'Indore': [22.7196, 75.8577]
}

# ========== CREATE MAP ==========
# Center map on India
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles='cartodbpositron')

# ========== ADD MMLPs ==========
mmlps = ['Delhi', 'Mumbai', 'Chennai', 'Bengaluru', 'Nagpur', 'Jogighopa']
for mmlp in mmlps:
    if mmlp in city_coords:
        folium.Marker(
            location=city_coords[mmlp],
            popup=f"<b>{mmlp}</b><br>🏭 MMLP Hub",
            icon=folium.Icon(color='blue', icon='industry', prefix='fa'),
            tooltip=f"{mmlp} MMLP"
        ).add_to(m)

# ========== ADD ORIGIN & DESTINATION ==========
if r['origin'] in city_coords:
    folium.Marker(
        location=city_coords[r['origin']],
        popup=f"<b>{r['origin']}</b><br>📍 Origin",
        icon=folium.Icon(color='green', icon='play', prefix='fa'),
        tooltip=f"Origin: {r['origin']}"
    ).add_to(m)

if r['destination'] in city_coords:
    folium.Marker(
        location=city_coords[r['destination']],
        popup=f"<b>{r['destination']}</b><br>📍 Destination",
        icon=folium.Icon(color='red', icon='flag', prefix='fa'),
        tooltip=f"Destination: {r['destination']}"
    ).add_to(m)

# ========== PLOT ROUTE WITH CORRECT COLORS ==========
mode_colors = {
    'road': '#EF4444',    # Red
    'rail': '#3B82F6',    # Blue
    'sea': '#14B8A6',     # Teal
    'iwt': '#8B5CF6'      # Purple
}

# Parse route with modes
route_segments = []
for leg in r['optimal_path']:
    if 'Travel:' in leg:
        parts = leg.replace('Travel: ', '').split(' by ')
        cities = parts[0].split(' → ')
        mode = parts[1].lower()
        route_segments.append({
            'from': cities[0],
            'to': cities[1],
            'mode': mode,
            'color': mode_colors.get(mode, '#6B7280')
        })

# Draw each segment with its mode color
for segment in route_segments:
    if segment['from'] in city_coords and segment['to'] in city_coords:
        folium.PolyLine(
            locations=[city_coords[segment['from']], city_coords[segment['to']]],
            color=segment['color'],
            weight=5,
            opacity=0.9,
            popup=f"<b>{segment['from']} → {segment['to']}</b><br>Mode: {segment['mode'].upper()}",
            tooltip=f"{segment['from']} → {segment['to']} by {segment['mode']}"
        ).add_to(m)

# Draw MMLPs as separate layer (not interfering with route)
for mmlp in mmlps:
    if mmlp in city_coords:
        folium.Marker(
            location=city_coords[mmlp],
            popup=f"<b>{mmlp}</b><br>🏭 MMLP Hub",
            icon=folium.Icon(color='blue', icon='industry', prefix='fa'),
            tooltip=f"{mmlp} MMLP"
        ).add_to(m)

# ========== DISPLAY MAP ==========
col1, col2 = st.columns([3, 1])

with col1:
    folium_static(m, width=900, height=600)

with col2:
    st.markdown("### 🎨 Map Legend")
    
    st.markdown("""
    **📍 Markers:**
    - 🟢 Green: Origin
    - 🔴 Red: Destination  
    - 🔵 Blue: MMLP Hub
    
    **🛣️ Route Colors:**
    - 🔴 Red: Road
    - 🔵 Blue: Rail
    - 🟢 Teal: Sea
    - 🟣 Purple: IWT
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Route Summary")
    
    st.metric("Total Distance", f"{r['distance']:,.0f} km")
    st.metric("Total Time", f"{r['total_time_hours']:.0f} hours")
    st.metric("MMLPs Used", len([l for l in r['optimal_path'] if 'Transfer at' in l]))
    
    st.markdown("---")
    st.markdown("### 📌 Selected Vehicles")
    
    if 'vehicles_used' in r:
        for mode, v in r['vehicles_used'].items():
            st.markdown(f"- {v.get('emoji', '🚚')} **{mode.upper()}**: {v.get('name', mode)}")

# ========== NAVIGATION ==========
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("← Back to Overview", use_container_width=True):
        st.session_state.page = 'Overview'
        st.switch_page("pages/1_📊_Overview.py")

with col2:
    if st.button("💰 Cost & Emissions", use_container_width=True):
        st.session_state.page = 'Cost & Emissions'
        st.switch_page("pages/3_💰_Cost_&_Emissions.py")

with col3:
    if st.button("📋 Detailed Breakdown", use_container_width=True):
        st.session_state.page = 'Detailed'
        st.switch_page("pages/4_📋_Detailed_Breakdown.py")
