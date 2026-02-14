import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Detailed Breakdown", page_icon="📋", layout="wide")

if 'optimization_result' not in st.session_state or st.session_state.optimization_result is None:
    st.warning("⚠️ No optimization results found. Please run an optimization first.")
    if st.button("← Back to Home"):
        st.session_state.page = 'Home'
        st.switch_page("app.py")
    st.stop()

r = st.session_state.optimization_result

st.markdown("# 📋 Detailed Route Breakdown")
st.markdown("### Leg-by-Leg Analysis with Cost, CO₂, Time, and Vehicle Requirements")
st.markdown("---")

# ========== SECTION 1: UNIFIED LEG TABLE ==========
st.markdown("### 📍 Complete Route Log")

# Build unified table data
table_data = []
leg_number = 1
total_cost = 0
total_co2 = 0
total_time = 0
total_distance = 0
vehicle_counter = {}

if 'leg_details' in r:
    for leg in r['leg_details']:
        if leg.get('type') == 'travel':
            # Travel leg
            mode = leg.get('mode', 'unknown').upper()
            from_city = leg.get('from', '')
            to_city = leg.get('to', '')
            distance = leg.get('distance', 0)
            cost = leg.get('cost', 0)
            co2 = leg.get('co2', 0) 
            time_hrs = leg.get('time', 0)
            vehicles = leg.get('vehicles_needed', 0)
            capacity = leg.get('capacity', '?')
            
            # Track totals
            total_cost += cost
            total_co2 += co2
            total_time += time_hrs
            total_distance += distance
            
            # Track vehicles by mode
            if mode not in vehicle_counter:
                vehicle_counter[mode] = 0
            vehicle_counter[mode] += vehicles
            
            table_data.append({
                'Leg': leg_number,
                'Type': ' TRAVEL',
                'From → To': f"{from_city} → {to_city}",
                'Mode': mode,
                'Distance (km)': f"{distance:,.0f}",
                'Cost (₹)': f"₹{cost:,.0f}",
                'CO₂ (kg)': f"{co2:.1f}",
                'Time (h)': f"{time_hrs:.1f}",
                'Vehicles': f"{vehicles} × {capacity}t",
                'Details': f"{mode} {from_city}→{to_city}"
            })
            leg_number += 1
            
        elif leg.get('type') == 'transfer':
            # Transfer leg
            city = leg.get('city', '')
            from_mode = leg.get('from_mode', '').upper()
            to_mode = leg.get('to_mode', '').upper()
            
            # Get transfer cost
            if 'total_cost' in leg:
                transfer_cost = leg['total_cost']
            elif 'cost_per_tonne' in leg:
                tonnes = r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
                transfer_cost = leg['cost_per_tonne'] * tonnes
            else:
                transfer_cost = 600 * r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
            
            transfer_time = leg.get('transfer_time', 4)
            
            total_cost += transfer_cost
            total_time += transfer_time
            
            table_data.append({
                'Leg': '',
                'Type': ' TRANSFER',
                'From → To': f"{from_mode} → {to_mode}",
                'Mode': 'TRANSFER',
                'Distance (km)': '-',
                'Cost (₹)': f"₹{transfer_cost:,.0f}",
                'CO₂ (kg)': '0',
                'Time (h)': f"{transfer_time:.1f}",
                'Vehicles': '-',
                'Details': f"Transfer at {city}: {from_mode}→{to_mode}"
            })

# Create DataFrame
if table_data:
    df_display = pd.DataFrame(table_data)
    
    # Display with better column config
    st.dataframe(
        df_display[['Leg', 'Type', 'From → To', 'Mode', 'Distance (km)', 
                   'Cost (₹)', 'CO₂ (kg)', 'Time (h)', 'Vehicles']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'Leg': st.column_config.TextColumn('Leg', width='small'),
            'Type': st.column_config.TextColumn('Type', width='small'),
            'From → To': st.column_config.TextColumn('Route', width='medium'),
            'Mode': st.column_config.TextColumn('Mode', width='small'),
            'Distance (km)': st.column_config.TextColumn('Dist (km)', width='small'),
            'Cost (₹)': st.column_config.TextColumn('Cost', width='small'),
            'CO₂ (kg)': st.column_config.TextColumn('CO₂', width='small'),
            'Time (h)': st.column_config.TextColumn('Time', width='small'),
            'Vehicles': st.column_config.TextColumn('Vehicles', width='small')
        }
    )
else:
    st.warning("No leg details available")

# ========== SECTION 2: TOTALS ==========
st.markdown("---")
st.markdown("### 📊 Total Summary")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Total Distance", f"{total_distance:,.0f} km" if total_distance > 0 else "N/A")
with col2:
    st.metric("Total Cost", f"₹{total_cost:,.0f}" if total_cost > 0 else "N/A")
with col3:
    st.metric("Total CO₂", f"{total_co2:.1f} kg" if total_co2 > 0 else "N/A")
with col4:
    st.metric("Total Time", f"{total_time:.1f} hours" if total_time > 0 else "N/A")
with col5:
    total_vehicles = sum(vehicle_counter.values())
    st.metric("Total Vehicles", f"{total_vehicles}" if total_vehicles > 0 else "N/A")
with col6:
    tonnes = r.get('shipment_tonnes')
    st.metric("No. Of Tonnes", f"{tonnes}")

# ========== SECTION 3: VEHICLE SUMMARY ==========
if vehicle_counter:
    st.markdown("---")
    st.markdown("### 🚛 Vehicle Summary")
    
    vehicle_data = []
    for mode, count in vehicle_counter.items():
        # Find vehicle details from leg_details
        vehicle_info = {'capacity': '?', 'type': mode}
        for leg in r.get('leg_details', []):
            if leg.get('type') == 'travel' and leg.get('mode', '').upper() == mode:
                if 'capacity' in leg:
                    vehicle_info['capacity'] = leg['capacity']
                if 'vehicles_used' in r and mode.lower() in r['vehicles_used']:
                    vehicle_info = r['vehicles_used'][mode.lower()]
                break
        
        capacity = vehicle_info.get('capacity', '?')
        vehicle_name = vehicle_info.get('name', f'{mode} Vehicle')
        
        vehicle_data.append({
            'Mode': mode,
            'Vehicle Type': vehicle_name,
            'Count': count,
            'Capacity (t)': capacity,
            'Total Capacity (t)': count * capacity if isinstance(capacity, (int, float)) else '?'
        })
    
    vehicle_df = pd.DataFrame(vehicle_data)
    st.dataframe(vehicle_df, use_container_width=True, hide_index=True)

# ========== SECTION 4: EXPORT ==========
st.markdown("---")
st.markdown("### 📤 Export Data")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # CSV Export - Full table (clean encoding, NO EMOJIS)
    if 'table_data' in locals() and table_data:
        # Get shipment details
        shipment_tonnes = r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
        
        # Create clean export DataFrame (NO EMOJIS)
        export_data = []
        leg_counter = 1
        total_time_all = 0  # Will calculate total including transfers
        
        for item in table_data:
            # Clean the Type field (remove emojis)
            clean_type = item['Type'].replace('🚚 ', '').replace('🔄 ', '').replace('TRAVEL', 'Travel').replace('TRANSFER', 'Transfer')
            
            # Parse From and To
            from_to = item['From → To']
            if ' → ' in from_to:
                from_city = from_to.split(' → ')[0]
                to_city = from_to.split(' → ')[1]
            else:
                from_city = from_to
                to_city = ''
            
            # Clean values
            distance_val = item['Distance (km)'].replace(',', '') if item['Distance (km)'] != '-' else '0'
            cost_val = item['Cost (₹)'].replace('₹', '').replace(',', '') if item['Cost (₹)'] != '-' else '0'
            co2_val = item['CO₂ (kg)'] if item['CO₂ (kg)'] != '-' else '0'
            time_val = item['Time (h)'] if item['Time (h)'] != '-' else '0'
            
            # Add to total time
            if time_val != '0':
                try:
                    total_time_all += float(time_val)
                except:
                    pass
            
            # For transfer rows, set mode properly
            if clean_type == 'Transfer':
                mode_display = 'TRANSFER'
                # Parse from_mode and to_mode from Details
                if ':' in item['Details']:
                    mode_part = item['Details'].split(':')[1].strip()
                    if '→' in mode_part:
                        from_mode, to_mode = mode_part.split('→')
                        from_city = from_mode.strip()
                        to_city = to_mode.strip()
            else:
                mode_display = item['Mode']
            
            export_item = {
                'Leg': item['Leg'] if item['Leg'] != '⚡' else str(leg_counter) + 'T',  # Mark transfers with T
                'Segment_Type': clean_type,
                'From': from_city,
                'To': to_city,
                'Mode': mode_display,
                'Distance_km': distance_val,
                'Cost_INR': cost_val,
                'CO2_kg': co2_val,
                'Time_hours': time_val,
                'Vehicles': item['Vehicles'] if item['Vehicles'] != '-' else '',
                'Notes': item['Details'].replace('⚡', '').replace('🔄', '').replace('🚚', '').strip()
            }
            export_data.append(export_item)
            
            if item['Leg'] != '⚡':  # Only increment for travel legs
                leg_counter += 1
        
        export_df = pd.DataFrame(export_data)
        
        # Calculate total time from all legs (already have total_time_all)
        
        # Create metadata header with totals
        metadata = f"""# MULTI-MODAL LOGISTICS OPTIMIZER - ROUTE EXPORT
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ========================================
# SHIPMENT DETAILS
# Origin: {r['origin']}
# Destination: {r['destination']}
# Shipment Weight: {shipment_tonnes:,.1f} tonnes
# Optimization Objective: {r.get('objective', 'cost').upper()}
#
# TOTALS
# Total Cost: {total_cost:.0f}
# Total CO₂: {total_co2:.1f} kg
# Total Time: {total_time_all:.1f} hours ({total_time_all/24:.1f} days)
# Total Distance: {total_distance:,.0f} km
# Total Vehicles: {total_vehicles}
#
# LEG DETAILS
# ========================================
"""
        
        # Convert to CSV without index
        csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
        
        # Combine metadata and data
        full_csv = metadata + csv_data
        
        # Add final total row as comment
        total_row = f"\n# FINAL TOTALS: Distance={total_distance}km  , Cost={total_cost}  , CO2={total_co2}kg  , Time={total_time_all}h"
        full_csv += total_row
        
        st.download_button(
            label="📊 Export Full Log (CSV)",
            data=full_csv,
            file_name=f"route_log_{r['origin']}_{r['destination']}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col2:
    # Enhanced Summary Export with proper totals
    if total_distance > 0:
        shipment_tonnes = r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
        
        # Calculate per-unit metrics
        cost_per_tonne = total_cost / shipment_tonnes if shipment_tonnes > 0 else 0
        co2_per_tonne = total_co2 / shipment_tonnes if shipment_tonnes > 0 else 0
        cost_per_km = total_cost / total_distance if total_distance > 0 else 0
        co2_per_km = total_co2 / total_distance if total_distance > 0 else 0
        
        # Get MMLP count
        mmlp_count = len([l for l in r.get('optimal_path', []) if 'Transfer at' in l])
        
        summary_data = {
            'Metric': [
                'REPORT INFORMATION',
                'Generated',
                'Origin', 
                'Destination', 
                '',
                'SHIPMENT DETAILS',
                'Weight (tonnes)', 
                'Optimization Objective',
                '',
                'TOTAL COSTS & EMISSIONS',
                'Total Cost (INR)', 
                'Total CO2 (kg)',
                'Total Time (hours)',
                'Total Time (days)',
                'Total Distance (km)',
                'Total Vehicles Used',
                'MMLPs Used',
                '',
                'PER UNIT METRICS',
                'Cost per Tonne (/t)',
                'CO₂ per Tonne (kg/t)',
                'Cost per km (/km)',
                'CO₂ per km (kg/km)',
                'Average Speed (km/h)'
            ],
            'Value': [
                '',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                r['origin'],
                r['destination'],
                '',
                '',
                f"{shipment_tonnes:,.1f}",
                r.get('objective', 'cost').upper(),
                '',
                '',
                f"{total_cost:,.0f}",
                f"{total_co2:.1f}",
                f"{total_time:.1f}",
                f"{total_time/24:.1f}",
                f"{total_distance:,.0f}",
                f"{total_vehicles}",
                f"{mmlp_count}",
                '',
                '',
                f"₹{cost_per_tonne:,.0f}",
                f"{co2_per_tonne:.1f}",
                f"{cost_per_km:,.0f}",
                f"{co2_per_km:.2f}",
                f"{total_distance/total_time:.1f}" if total_time > 0 else "N/A"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        csv_summary = summary_df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📊 Export Summary (CSV)",
            data=csv_summary,
            file_name=f"summary_{r['origin']}_{r['destination']}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col3:
    # Enhanced JSON Export with all totals
    shipment_tonnes = r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
    
    # Calculate all metrics
    cost_per_tonne = total_cost / shipment_tonnes if shipment_tonnes > 0 else 0
    co2_per_tonne = total_co2 / shipment_tonnes if shipment_tonnes > 0 else 0
    cost_per_km = total_cost / total_distance if total_distance > 0 else 0
    co2_per_km = total_co2 / total_distance if total_distance > 0 else 0
    
    # Create clean serializable dict with metadata
    export_json = {
        "report": {
            "generated": datetime.now().isoformat(),
            "version": "1.0",
            "tool": "Multi-Modal Logistics Optimizer"
        },
        "shipment": {
            "origin": r['origin'],
            "destination": r['destination'],
            "weight_tonnes": float(shipment_tonnes),
            "optimization_objective": r.get('objective', 'cost')
        },
        "totals": {
            "cost": {
                "total_inr": float(total_cost),
                "per_tonne": float(cost_per_tonne),
                "per_km": float(cost_per_km)
            },
            "emissions": {
                "total_co2_kg": float(total_co2),
                "per_tonne_kg": float(co2_per_tonne),
                "per_km_kg": float(co2_per_km)
            },
            "time": {
                "total_hours": float(total_time),
                "total_days": float(total_time / 24),
                "average_speed_kmh": float(total_distance / total_time) if total_time > 0 else 0
            },
            "distance": {
                "total_km": float(total_distance)
            },
            "vehicles": {
                "total_count": int(total_vehicles),
                "by_mode": {str(k): int(v) for k, v in vehicle_counter.items()}
            }
        },
        "legs": export_data if 'export_data' in locals() else []
    }
    
    json_data = json.dumps(export_json, indent=2, default=str)
    
    st.download_button(
        label="📁 Export JSON",
        data=json_data,
        file_name=f"route_{r['origin']}_{r['destination']}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )

with col4:
    # Quick Summary Card (clean, no emojis)
    shipment_tonnes = r.get('shipment_tonnes', r.get('amount', r.get('tonnes', 100)))
    
    st.markdown("### Shipment Summary")
    st.markdown(f"""
    **Route:** {r['origin']} → {r['destination']}
    **Weight:** {shipment_tonnes:,.1f} tonnes
    **Objective:** {r.get('objective', 'cost').upper()}
    
    **Total Cost:** ${total_cost:,.0f}
    **Total CO₂:** {total_co2:.1f} kg
    **Total Time:** {total_time:.1f} hours ({total_time/24:.1f} days)
    **Total Distance:** {total_distance:,.0f} km
    **Total Vehicles:** {total_vehicles}
    """)
    
    # PDF Export (placeholder)
    st.button(
        label="PDF Report",
        disabled=True,
        use_container_width=True,
        help="PDF export coming soon"
    )
# ========== SECTION 5: RAW DATA ==========
with st.expander("🔧 Raw Optimization Data"):
    st.json({k: str(v) if not isinstance(v, (int, float, dict, list)) else v for k, v in r.items()})

# ========== NAVIGATION ==========
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("← Back to Cost & Emissions", use_container_width=True):
        st.session_state.page = 'Cost & Emissions'
        st.switch_page("pages/3_💰_Cost_&_Emissions.py")

with col2:
    if st.button("🗺️ Route Map", use_container_width=True):
        st.session_state.page = 'Route Map'
        st.switch_page("pages/2_🗺️_Route_Map.py")

with col3:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'Home'
        st.switch_page("app.py")
