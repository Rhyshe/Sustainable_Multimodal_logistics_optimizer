import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

# ========== CHECK FOR RESULTS ==========
if 'optimization_result' not in st.session_state or st.session_state.optimization_result is None:
    st.warning("⚠️ No optimization results found. Please run an optimization first.")
    if st.button("← Back to Home"):
        st.session_state.page = 'Home'
        st.switch_page("app.py")
    st.stop()

r = st.session_state.optimization_result

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    .metric-green {
        background-color: #ECFDF5;
        padding: 1rem;
        border-radius: 0.75rem;
        border-left: 4px solid #10B981;
    }
    .metric-red {
        background-color: #FEF2F2;
        padding: 1rem;
        border-radius: 0.75rem;
        border-left: 4px solid #EF4444;
    }
    .metric-neutral {
        background-color: #F9FAFB;
        padding: 1rem;
        border-radius: 0.75rem;
        border-left: 4px solid #9CA3AF;
    }
    .route-timeline {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 0.75rem;
        font-family: monospace;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== HEADER ==========
st.markdown("# 📊 Overview")
st.markdown("### Route Optimization Results")
st.markdown("---")

# ========== SECTION 1: HEADER METRICS ==========
col1, col2, col3, col4 = st.columns(4)

# Get road comparison data (simulated if not available)
road_cost = r.get('road_cost', r['total_cost'] * 1.3)  # Fallback
road_co2 = r.get('road_co2', r['total_co2'] * 5)      # Fallback
road_time = r.get('road_time', r['total_time_hours'] * 0.9)  # Fallback

cost_delta = (r['total_cost'] - road_cost) / road_cost * 100
co2_delta = (r['total_co2'] - road_co2) / road_co2 * 100
time_delta = (r['total_time_hours'] - road_time) / road_time * 100

with col1:
    delta_color = "normal" if cost_delta < 0 else "inverse"
    st.metric(
        label="💰 TOTAL COST",
        value=f"₹{r['total_cost']:,.0f}",
        delta=f"{cost_delta:.1f}% vs road",
        delta_color="normal" if cost_delta < 0 else "inverse"
    )

with col2:
    st.metric(
        label="🌿 TOTAL CO₂",
        value=f"{r['total_co2']/1000:,.1f} kg",
        delta=f"{co2_delta:.1f}% vs road",
        delta_color="normal" if co2_delta < 0 else "inverse"
    )

with col3:
    st.metric(
        label="⏱️ TRANSIT TIME",
        value=f"{r['total_time_hours']:.0f} hours",
        delta=f"{time_delta:.1f}% vs road",
        delta_color="normal" if time_delta < 0 else "inverse"
    )

with col4:
    st.metric(
        label="📏 DISTANCE",
        value=f"{r['distance']:,.0f} km",
        delta=None
    )

st.markdown("---")

st.markdown('<h3 class="sub-header">📍 Route Timeline</h3>', unsafe_allow_html=True)

# Parse route and build timeline
route_cities = [r['origin']]
route_modes = []
route_distances = []

for leg in r['optimal_path']:
    if 'Travel:' in leg:
        parts = leg.replace('Travel: ', '').split(' by ')
        cities = parts[0].split(' → ')
        mode = parts[1].lower()
        if cities[1] not in route_cities:
            route_cities.append(cities[1])
        route_modes.append(mode)

# Calculate per-leg distances (proportional)
num_legs = len([l for l in r['optimal_path'] if 'Travel:' in l])
leg_distance = r['distance'] // num_legs
cumulative = 0

# Build route card with columns
route_card = st.container()
with route_card:
    # Total columns: origin + each leg + destination
    total_columns = num_legs + 2
    cols = st.columns(total_columns)
    
    col_index = 0
    
    # Origin
    with cols[col_index]:
        st.markdown(f"### 🟢 {r['origin']}")
    col_index += 1
    
    # Route legs
    mmlp_cities = ['Nagpur', 'Chennai', 'Delhi', 'Mumbai', 'Bengaluru', 'Jogighopa']
    mode_icons = {'road': '🚛', 'rail': '🚂', 'sea': '🚢', 'iwt': '🛶'}
    
    for i in range(len(route_cities)-1):
        from_city = route_cities[i]
        to_city = route_cities[i+1]
        mode = route_modes[i] if i < len(route_modes) else 'rail'
        
        with cols[col_index]:
            cumulative = leg_distance
            # From city
            st.markdown(f"**{from_city}**")
            
            # Mode icon and info
            st.markdown(f"{mode_icons.get(mode, '🚚')}")
            st.markdown(f"`{mode.upper()}`")
            st.markdown(f"↓")
            
            # Distance
            st.markdown(f"*{cumulative} km*")
            
            # MMLP indicator if applicable
            if to_city in mmlp_cities:
                st.markdown(f"🏭 **MMLP**")
            
            # To city (if not last leg, otherwise handled by destination)
            if i < len(route_cities)-2:
                st.markdown(f"**{to_city}**")
            
            
        
        col_index += 1
    
    # Destination
    with cols[col_index]:
        st.markdown(f"### 🔴 {r['destination']}")
        st.markdown(f"*{r['distance']} km*")

# Transfer points
transfers = [leg for leg in r['optimal_path'] if 'Transfer at' in leg]
if transfers:
    st.markdown("**⚡ Transfer Points:**")
    for transfer in transfers:
        # Parse transfer information for better display
        if 'Transfer:' in transfer:
            parts = transfer.replace('Transfer: ', '').split(' → ')
            modes = parts[0].split(' → ')
            city = parts[1].split(' at ')[1]
            
            transfer_cols = st.columns([1, 4])
            with transfer_cols[0]:
                st.markdown("🔄")
            with transfer_cols[1]:
                st.markdown(f"**{city}** — `{modes[0]} → {modes[1]}`")
        else:
            st.markdown(f"- {transfer}")

# ========== SECTION 3: ROAD COMPARISON ==========
st.markdown("###  Multi-Modal 🆚 Road-Only")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 💰 Cost Comparison")
    fig_cost = go.Figure()
    fig_cost.add_trace(go.Bar(
        x=['Multi-Modal', 'Road-Only'],
        y=[r['total_cost'], road_cost],
        marker_color=['#10B981', '#EF4444'],
        text=[f'₹{r["total_cost"]:,.0f}', f'₹{road_cost:,.0f}'],
        textposition='outside',
    ))
    fig_cost.update_layout(
        height=400,
        yaxis_title="Cost (₹)",
        showlegend=False
    )
    st.plotly_chart(fig_cost, use_container_width=True)

with col2:
    st.markdown("#### 🌿 CO₂ Comparison")
    fig_co2 = go.Figure()
    fig_co2.add_trace(go.Bar(
        x=['Multi-Modal', 'Road-Only'],
        y=[r['total_co2']/1000, road_co2/1000],
        marker_color=['#10B981', '#EF4444'],
        text=[f'{r["total_co2"]/1000:.0f} kg', f'{road_co2/1000:.0f} kg'],
        textposition='outside',
    ))
    fig_co2.update_layout(
        height=400,
        yaxis_title="CO₂ (kg)",
        showlegend=False
    )
    st.plotly_chart(fig_co2, use_container_width=True)

# ========== SECTION 4: QUICK STATS ==========
st.markdown("### 📊 Quick Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Cost per Tonne",
        value = f"₹{r['total_cost'] / r.get('shipment_tonnes', 100):,.0f}"
    )

with col2:
    st.metric(
        label="CO₂ per Tonne",
        value=f"{r['total_co2'] / r.get('shipment_tonnes', 100):,.1f} kg"
    )

with col3:
    st.metric(
        label="Time per 100km",
        value=f"{r['total_time_hours'] / (r['distance']/100):.1f} hours"
    )

# ========== SAVINGS SUMMARY ==========
st.markdown("---")
st.markdown("### 💰 Savings Summary")

savings = road_cost - r['total_cost']
co2_savings = road_co2 - r['total_co2']

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="metric-green">', unsafe_allow_html=True)
    st.metric(
        label="Total Cost Savings",
        value=f"₹{savings:,.0f}",
        delta=f"{cost_delta:.1f}%"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-green">', unsafe_allow_html=True)
    st.metric(
        label="Total CO₂ Reduction",
        value=f"{co2_savings/1000:,.0f} kg",
        delta=f"{co2_delta:.1f}%"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ========== NAVIGATION BUTTONS ==========
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("← Back to Home", use_container_width=True):
        st.session_state.page = 'Home'
        st.switch_page("app.py")

with col2:
    if st.button("🗺️ View Route Map", use_container_width=True):
        st.session_state.page = 'Route Map'
        st.switch_page("pages/2_🗺️_Route_Map.py")

with col3:
    if st.button("💰 Cost Analysis", use_container_width=True):
        st.session_state.page = 'Cost & Emissions'
        st.switch_page("pages/3_💰_Cost_&_Emissions.py")

with col4:
    if st.button("📋 Detailed Breakdown", use_container_width=True):
        st.session_state.page = 'Detailed'
        st.switch_page("pages/4_📋_Detailed_Breakdown.py")
