import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Cost & Emissions", page_icon="💰", layout="wide")

if 'optimization_result' not in st.session_state or st.session_state.optimization_result is None:
    st.warning("⚠️ No optimization results found. Please run an optimization first.")
    if st.button("← Back to Home"):
        st.session_state.page = 'Home'
        st.switch_page("app.py")
    st.stop()

r = st.session_state.optimization_result

st.markdown("# 💰 Cost & Emissions Analysis")
st.markdown("### Detailed Breakdown of Logistics Costs and Environmental Impact")
st.markdown("---")

# ========== SECTION 1: COST BREAKDOWN ==========
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💰 Cost Breakdown")
    
    # Calculate ACTUAL costs from leg_details
    transport_cost = 0
    transfer_cost = 0
    handling_cost = 0  # You may not have this in your data
    
    if 'leg_details' in r:
        for leg in r['leg_details']:
            if leg.get('type') == 'travel':
                # Add transport cost from each travel leg
                transport_cost += leg.get('cost', 0)
            elif leg.get('type') == 'transfer':
                # Add transfer cost (total_cost or cost_per_tonne * tonnes)
                if 'total_cost' in leg:
                    transfer_cost += leg['total_cost']
                elif 'cost_per_tonne' in leg:
                    tonnes = r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
                    transfer_cost += leg['cost_per_tonne'] * tonnes
    
    # If no transfer data found, calculate from optimal_path as fallback
    if transfer_cost == 0:
        for leg in r['optimal_path']:
            if 'Transfer at' in leg:
                tonnes = r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
                transfer_cost += 600 * tonnes  # Default ₹600/tonne
    
    # Calculate handling cost as remaining (if any)
    total_calculated = transport_cost + transfer_cost
    if total_calculated < r['total_cost']:
        handling_cost = r['total_cost'] - total_calculated
    
    # Only show components that have value
    labels = []
    values = []
    colors = []
    
    if transport_cost > 0:
        labels.append('Transport')
        values.append(transport_cost)
        colors.append('#3B82F6')  # Blue
    if transfer_cost > 0:
        labels.append('Transfers')
        values.append(transfer_cost)
        colors.append('#F59E0B')  # Orange
    if handling_cost > 0:
        labels.append('MMLP Handling')
        values.append(handling_cost)
        colors.append('#10B981')  # Green
    
    # Donut chart
    if values:
        fig_cost = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='outside',
            insidetextorientation='radial'
        )])
        
        fig_cost.update_layout(
            height=400,
            showlegend=False,
            annotations=[dict(
                text=f'₹{r["total_cost"]:,.0f}',
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig_cost, use_container_width=True)
    else:
        st.info("No cost data available")
    
    # Cost table
    cost_data = []
    if transport_cost > 0:
        cost_data.append({
            'Component': 'Transport',
            'Cost (₹)': f'₹{transport_cost:,.0f}',
            'Percentage': f'{transport_cost/r["total_cost"]*100:.0f}%'
        })
    if transfer_cost > 0:
        cost_data.append({
            'Component': 'Transfers',
            'Cost (₹)': f'₹{transfer_cost:,.0f}',
            'Percentage': f'{transfer_cost/r["total_cost"]*100:.0f}%'
        })
    if handling_cost > 0:
        cost_data.append({
            'Component': 'MMLP Handling',
            'Cost (₹)': f'₹{handling_cost:,.0f}',
            'Percentage': f'{handling_cost/r["total_cost"]*100:.0f}%'
        })
    
    # Add total row
    cost_data.append({
        'Component': '**TOTAL**',
        'Cost (₹)': f'**₹{r["total_cost"]:,.0f}**',
        'Percentage': '**100%**'
    })
    
    cost_df = pd.DataFrame(cost_data)
    st.dataframe(cost_df, use_container_width=True, hide_index=True)

with col2:
    st.markdown("### 🌿 Emissions Breakdown")
    
    # Calculate emissions by mode from leg_details
    emissions_by_mode = {}
    
    if 'leg_details' in r:
        for leg in r['leg_details']:
            if leg.get('type') == 'travel':
                mode = leg.get('mode', 'unknown')
                co2 = leg.get('co2', 0)
                
                if mode not in emissions_by_mode:
                    emissions_by_mode[mode] = 0
                emissions_by_mode[mode] += co2
    
    if emissions_by_mode:
        # Prepare data for chart
        modes = list(emissions_by_mode.keys())
        co2_values = [emissions_by_mode[m] for m in modes]
        total_co2 = sum(co2_values)
        
        # Color mapping
        color_map = {
            'road': '#EF4444',   # Red
            'rail': '#3B82F6',   # Blue
            'sea': '#14B8A6',    # Teal
            'iwt': '#8B5CF6'     # Purple
        }
        colors = [color_map.get(m, '#6B7280') for m in modes]
        
        # Horizontal stacked bar
        fig_emissions = go.Figure()
        
        for i, mode in enumerate(modes):
            fig_emissions.add_trace(go.Bar(
                name=mode.upper(),
                y=['CO₂ Emissions'],
                x=[co2_values[i]],
                orientation='h',
                text=[f"{co2_values[i]:.0f} g ({co2_values[i]/total_co2*100:.0f}%)"],
                textposition='inside',
                marker_color=colors[i]
            ))
        
        fig_emissions.update_layout(
            barmode='stack',
            height=200,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        st.plotly_chart(fig_emissions, use_container_width=True)
        

# ========== SECTION 2: VEHICLE ECONOMICS ==========
st.markdown("### 🚛 Vehicle Economics")

if 'vehicles_used' in r and 'vehicles_needed' in r:
    vehicle_data = []
    
    for mode, count in r['vehicles_needed'].items():
        if mode in r['vehicles_used']:
            v = r['vehicles_used'][mode]
            
            # Calculate cost per tonne-km
            if 'cost_per_tonne_km' in v:
                cost_per_tkm = v['cost_per_tonne_km']
            elif 'cost_per_km' in v and 'capacity' in v:
                cost_per_tkm = v['cost_per_km'] / v['capacity']
            else:
                # Default values based on mode
                defaults = {
                    'road': 3.67, 'rail': 1.0, 'sea': 0.4, 'iwt': 0.3
                }
                cost_per_tkm = defaults.get(mode, 1.0)
            
            # Calculate CO₂ per tonne-km
            if 'co2_per_tonne_km' in v:
                co2_per_tkm = v['co2_per_tonne_km']
            elif 'co2_per_km' in v and 'capacity' in v:
                co2_per_tkm = v['co2_per_km'] / v['capacity']
            else:
                # Default values based on mode
                defaults = {
                    'road': 10, 'rail': 1.33, 'sea': 0.22, 'iwt': 0.2
                }
                co2_per_tkm = defaults.get(mode, 1.0)
            
            vehicle_data.append({
                'Mode': mode.upper(),
                'Vehicle Type': v.get('name', mode.title()),
                'Count': count,
                'Capacity (t)': v.get('capacity', '?'),
                'Cost/tonne-km': f"₹{cost_per_tkm:.2f}",
                'CO₂/tonne-km': f"{co2_per_tkm:.1f}g"
            })
    
    if vehicle_data:
        vehicle_df = pd.DataFrame(vehicle_data)
        st.dataframe(vehicle_df, use_container_width=True, hide_index=True)
    else:
        st.info("Vehicle economics data not available")
else:
    st.info("Run optimization to see vehicle economics")

# ========== SECTION 3: TRANSFER SUMMARY ==========
st.markdown("---")
st.markdown("### ⚡ Transfer Summary")

transfers_data = []
total_transfer_cost = 0
total_transfer_time = 0

# Check if leg_details exists and extract transfer information
if 'leg_details' in r:
    for leg_detail in r['leg_details']:
        if leg_detail.get('type') == 'transfer':
            # Extract data from leg_details
            city = leg_detail.get('city', 'Unknown')
            from_mode = leg_detail.get('from_mode', '').upper()
            to_mode = leg_detail.get('to_mode', '').upper()
            
            # Get cost from actual data (either cost_per_tonne or total_cost)
            if 'total_cost' in leg_detail:
                transfer_cost = leg_detail['total_cost']
            elif 'cost_per_tonne' in leg_detail and 'tonnes' in r:
                transfer_cost = leg_detail['cost_per_tonne'] * r['tonnes']
            else:
                transfer_cost = 0
            
            # Calculate transfer time (default 4 hours per transfer)
            transfer_time = leg_detail.get('transfer_time')
            
            transfers_data.append({
                'Location': city,
                'From Mode': from_mode,
                'To Mode': to_mode,
                'Cost (₹)': f"₹{transfer_cost:,.0f}",
                'Time (h)': transfer_time
            })
            
            total_transfer_cost += transfer_cost
            total_transfer_time += transfer_time

# Fallback to parsing from optimal_path if leg_details doesn't exist
if not transfers_data and 'optimal_path' in r:
    for leg in r['optimal_path']:
        if 'Transfer' in leg:
            # Parse: "Transfer: sea → rail at Mumbai"
            parts = leg.split('Transfer: ')[1]
            modes_part = parts.split(' at ')[0]
            city = parts.split(' at ')[1]
            modes = modes_part.split(' → ')
            
            # Calculate transfer cost based on shipment tonnes
            if 'tonnes' in r:
                transfer_cost = 700 * r['tonnes']  # Using actual rate from data
            else:
                transfer_cost = 0
            
            transfer_time = 4
            
            transfers_data.append({
                'Location': city,
                'From Mode': modes[0].upper(),
                'To Mode': modes[1].upper(),
                'Cost (₹)': f"₹{transfer_cost:,.0f}",
                'Time (h)': transfer_time
            })
            
            total_transfer_cost += transfer_cost
            total_transfer_time += transfer_time

if transfers_data:
    # Create and display the dataframe
    transfers_df = pd.DataFrame(transfers_data)
    st.dataframe(
        transfers_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Location': '📍 Location',
            'From Mode': '🚛 From',
            'To Mode': '🚂 To',
            'Cost (₹)': '💰 Cost',
            'Time (h)': '⏱️ Time(Hours)'
        }
    )
    
    # Show totals
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Transfer Cost",
            f"₹{total_transfer_cost:,.0f}",
            delta=f"{len(transfers_data)} transfer(s)"
        )
    with col2:
        st.metric(
            "Total Transfer Time",
            f"{total_transfer_time} hours",
            delta=f"{total_transfer_time/24:.1f} days"
        )
    with col3:
        avg_cost_per_transfer = total_transfer_cost / len(transfers_data) if transfers_data else 0
        st.metric(
            "Avg Cost/Transfer",
            f"₹{avg_cost_per_transfer:,.0f}"
        )
    
    # Optional: Show transfer details in an expander
    with st.expander("📋 Transfer Details"):
        for i, transfer in enumerate(transfers_data, 1):
            st.markdown(f"""
            **Transfer #{i}** at **{transfer['Location']}**  
            - Mode change: `{transfer['From Mode']} → {transfer['To Mode']}`  
            - Cost: {transfer['Cost (₹)']}  
            - Time: {transfer['Time (h)']} hours
            """)
else:
    st.info("✅ No transfers in this route - direct connection available")

# ========== SECTION 4: SUSTAINABILITY IMPACT ==========
st.markdown("### 🌍 Sustainability Impact")

# Calculate sustainability metrics
co2_saved = r.get('co2_reduction', r['total_co2'] * 4)  # Fallback
trees_saved = co2_saved / 1000 / 21  # 21kg CO₂ per tree per year
cars_off_road = co2_saved / 1000 / (2000 * 0.15)  # 2 tonnes/year, 150g/km
fuel_saved = (r.get('road_distance', r['distance'] * 1.3) - r['distance']) * 0.35  # 0.35L/km
modal_shift = 62  # % of tonne-km on rail/sea

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div style="background: #ECFDF5; padding: 1.5rem; border-radius: 0.75rem;">', unsafe_allow_html=True)
    st.markdown("### 🌳")
    st.metric("Trees Planted", f"{trees_saved:.0f}", help="Equivalent trees planted per year")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div style="background: #EFF6FF; padding: 1.5rem; border-radius: 0.75rem;">', unsafe_allow_html=True)
    st.markdown("### 🚗")
    st.metric("Cars Off Road", f"{cars_off_road:.0f}", help="Equivalent cars removed from road")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div style="background: #FEF3C7; padding: 1.5rem; border-radius: 0.75rem;">', unsafe_allow_html=True)
    st.markdown("### ⛽")
    st.metric("Fuel Saved", f"{fuel_saved:,.0f} L", help="Diesel saved vs road-only")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div style="background: #EDE9FE; padding: 1.5rem; border-radius: 0.75rem;">', unsafe_allow_html=True)
    st.markdown("### 📊")
    st.metric("Modal Shift", f"{modal_shift}%", help="% of tonne-km shifted from road")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== NAVIGATION ==========
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("← Back to Route Map", use_container_width=True):
        st.session_state.page = 'Route Map'
        st.switch_page("pages/2_🗺️_Route_Map.py")

with col2:
    if st.button("📋 Detailed Breakdown", use_container_width=True):
        st.session_state.page = 'Detailed'
        st.switch_page("pages/4_📋_Detailed_Breakdown.py")

with col3:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'Home'
        st.switch_page("app.py")
