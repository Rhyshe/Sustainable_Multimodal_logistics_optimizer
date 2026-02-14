import streamlit as st
import pandas as pd
import numpy as np
from optimizer_engine import calculate_shipment_optimized, mmlps, G, vehicle_types, default_vehicles

import sys
import subprocess
import os

print("="*50)
print("🔍 DEBUG INFORMATION")
print("="*50)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

# Try to import networkx
try:
    import networkx
    print(f"✅ NetworkX found! Version: {networkx.__version__}")
except ImportError as e:
    print(f"❌ NetworkX import failed: {e}")
    
    # List installed packages
    print("\n📦 Installed packages:")
    subprocess.call([sys.executable, "-m", "pip", "list"])
print("="*50)


# ========== PAGE CONFIG ==========
st.set_page_config(page_title="Multi-Modal Logistics Optimizer", page_icon="🚗", layout="wide")

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #6B7280;
        margin-top: 0;
    }
    .stat-card {
        background-color: #F9FAFB;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #E5E7EB;
        text-align: center;
    }
    .mmlp-badge {
        background-color: #EFF6FF;
        color: #1E40AF;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.25rem;
    }
    .stButton > button {
        background-color: #2563EB;
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        font-size: 1.2rem;
        border-radius: 0.5rem;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #1E40AF;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if 'optimization_result' not in st.session_state:
    st.session_state.optimization_result = None
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# ========== HEADER ==========
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h1 class="main-header">🚛 Multi-Modal Logistics Optimizer</h1>', unsafe_allow_html=True)
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3095/3095109.png", width=100)

st.markdown("---")

# ========== MAIN CONTENT ==========
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### 📦 Shipment Details")
    
    with st.container():
        # Origin and Destination
        cities = sorted(['Delhi', 'Mumbai', 'Chennai', 'Bengaluru', 'Kolkata', 
                        'Hyderabad', 'Ahmedabad', 'Pune', 'Nagpur', 'Jogighopa',
                        'Guwahati', 'Kochi', 'Goa', 'Vizag', 'Lucknow', 'Jaipur'])
        
        col1, col2 = st.columns(2)
        with col1:
            origin = st.selectbox("Origin City", cities, index=0)
        with col2:
            destination = st.selectbox("Destination City", cities, index=3)
        
        # Tonnage
        tonnes = st.slider("Shipment Weight (tonnes)", min_value=1, max_value=1000, value=100, step=10)
        
        st.markdown("---")
        st.markdown("### 🎯 Optimization Objective")
        
        # Objective selection
        objective = st.radio(
            "Choose optimization priority",
            options=['Cost', 'CO2', 'Time', 'Balanced'],
            horizontal=True,
            index=0
        )
        
        # Weight sliders for Balanced
        weights = None
        if objective == 'Balanced':
            st.markdown("##### Set Importance Weights")
            col1, col2, col3 = st.columns(3)
            with col1:
                w_cost = st.slider("Cost", 0.0, 1.0, 0.4, 0.1)
            with col2:
                w_co2 = st.slider("co2", 0.0, 1.0, 0.3, 0.1)
            with col3:
                w_time = st.slider("Time", 0.0, 1.0, 0.3, 0.1)
            
            # Normalize to sum to 1
            total = w_cost + w_co2 + w_time
            weights = {
                'cost': w_cost / total,
                'co2': w_co2 / total,
                'time': w_time / total
            }
        
        st.markdown("---")
        st.markdown("### 🚛 Vehicle Fleet Selection")
        
        # Vehicle selection
        col1, col2 = st.columns(2)
        with col1:
            road_vehicle = st.selectbox(
                "Road Trucks",
                options=['light_truck', 'standard_truck', 'heavy_truck'],
                format_func=lambda x: {
                    'light_truck': '🚛 Light Truck (7.5t)',
                    'standard_truck': '🚛 Standard Truck (15t)',
                    'heavy_truck': '🚛 Heavy Truck (25t)'
                }.get(x, x),
                index=1
            )
            
            rail_vehicle = st.selectbox(
                "Rail Wagons",
                options=['standard_wagon', 'double_stack'],
                format_func=lambda x: {
                    'standard_wagon': '🚂 Standard Wagon (22.5t)',
                    'double_stack': '🚂 Double-Stack Wagon (45t)'
                }.get(x, x),
                index=0
            )
        
        with col2:
            sea_vehicle = st.selectbox(
                "Sea Vessels",
                options=['coastal_roro', 'small_roro'],
                format_func=lambda x: {
                    'coastal_roro': '🚢 Coastal Ro-Ro (225t)',
                    'small_roro': '🚢 Small Ro-Ro (150t)'
                }.get(x, x),
                index=0
            )
            
            iwt_vehicle = st.selectbox(
                "IWT Barges",
                options=['iwt_barge'],
                format_func=lambda x: {
                    'iwt_barge': '🛶 IWT Barge (150t)'
                }.get(x, x),
                index=0
            )
        
        selected_vehicles = {
            'road': road_vehicle,
            'rail': rail_vehicle,
            'sea': sea_vehicle,
            'iwt': iwt_vehicle
        }
# ========== OPTIMIZE BUTTON ==========
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    optimize_clicked = st.button("🚀 OPTIMIZE ROUTE", use_container_width=True)
    

# ========== RUN OPTIMIZATION ==========
if optimize_clicked:
    with st.spinner("Finding optimal route across 4 transport modes..."):
        try:
            result = calculate_shipment_optimized(
                tonnes=tonnes,
                origin=origin,
                destination=destination,
                mmlps=['Nagpur', 'Bengaluru', 'Jogighopa', 'Chennai', 'Delhi', 'Mumbai'],
                objective=objective.lower(),
                weights=weights,
                selected_vehicles=selected_vehicles
            )
            
            if result:
                st.session_state.optimization_result = result
                st.session_state.page = 'Overview'
                st.success("✅ Optimal route found! Redirecting to results...")
                st.rerun()
            else:
                st.error("❌ No route found between these cities. Try different combination.")
        except Exception as e:
            st.error(f"❌ Optimization failed: {str(e)}")

# ========== SIDEBAR NAVIGATION ==========
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    
    pages = {
        'Home': '🏠 Home',
        'Overview': '📊 Overview',
        'Route Map': '🗺️ Route Map',
        'Cost & Emissions': '💰 Cost & Emissions',
        'Detailed': '📋 Detailed Breakdown'
    }
    
    for page_key, page_name in pages.items():
        if st.button(page_name, use_container_width=True, key=f"nav_{page_key}"):
            st.session_state.page = page_key
            st.rerun()
    
    
    with st.container():
        st.metric("Cities Connected", "25")
        
        st.metric("MMLP Hubs", "6")
        
       
        
  
        st.metric("Transport Modes", "4")
        
    
    st.markdown("---")
    st.markdown("### 🏭 MMLP Locations")
    
    mmlp_html = ""
    for mmlp in ['Delhi', 'Mumbai', 'Chennai', 'Bengaluru', 'Nagpur', 'Jogighopa']:
        st.markdown(f"📍 **{mmlp}**")
    
    st.markdown("---")
    st.markdown("### 📌 Assumptions")
    st.markdown("• Vehicles available at all MMLPs\n")
    st.markdown("• Unlimited fleet size\n")
    st.markdown("• Standard emission factors\n")
    st.markdown("• No weather delays")
 

# ========== PAGE ROUTING ==========
if st.session_state.page == 'Home':
    pass  # We're already on Home
elif st.session_state.page == 'Overview':
    st.switch_page("pages/1_📊_Overview.py")
elif st.session_state.page == 'Route Map':
    st.switch_page("pages/2_🗺️_Route_Map.py")
elif st.session_state.page == 'Cost & Emissions':
    st.switch_page("pages/3_💰_Cost_&_Emissions.py")
elif st.session_state.page == 'Detailed':
    st.switch_page("pages/4_📋_Detailed_Breakdown.py")


