
import pandas as pd

df = pd.read_csv("indian_multimodal_distances.csv")


import networkx as nx

G = nx.MultiDiGraph()

for _, row in df.iterrows():
  from_city = row['from']
  to_city = row['to']

  if row['road_km'] > 0:
    G.add_edge(from_city, to_city, mode='road', distance=row['road_km'])
    G.add_edge(to_city, from_city, mode = 'road', distance  = row['road_km'])

  if row['rail_km'] > 0:
    G.add_edge(from_city, to_city, mode='rail', distance =row['rail_km'])
    G.add_edge(to_city, from_city, mode='rail', distance =row['rail_km'])


  if row['sea_km'] > 0:
    G.add_edge(from_city, to_city, mode='sea', distance = row['sea_km'])
    G.add_edge(to_city, from_city, mode='sea', distance = row['sea_km'])


  if row['iwt_km'] > 0:
    G.add_edge(from_city, to_city, mode='iwt', distance = row['iwt_km'])
    G.add_edge(to_city, from_city, mode='iwt', distance = row['iwt_km'])



def shortest_road_path(G, source, target):
  road_G = nx.DiGraph()
  edge_info = {}

  for u, v, data in G.edges(data=True):
    if data.get('mode') == 'road':
      current_weight = road_G.get_edge_data(u, v, {}).get('weight', float('inf'))
      new_weight = float(data['distance'])
      if new_weight < current_weight:
        road_G.add_edge(u, v, weight=new_weight)
        edge_info[(u, v)] = data

  try:
    path = nx.shortest_path(road_G, source=source, target = target, weight = 'weight')
    distance = nx.shortest_path_length(road_G, source = source, target = target, weight = 'weight')

    edges_used = []
    for i in range(len(path)-1):
      u, v = path[i], path[i+1]
      edges_used.append(edge_info.get((u, v), {}))

    return path, distance, edges_used
  except nx.NetworkXNoPath:
    return None, None, None

path, dist, edges_road = shortest_road_path(G, 'Delhi', 'Hyderabad')
print(f"Path: {path}, Distance: {dist}Km")

path, dist, edges = shortest_road_path(G, 'Delhi', 'Hyderabad')
print(f"Path: {path}, Distance: {dist}")




cost_per_km = {  #This is per cost_per_km per car
    'road' : 5.5,
    'rail' : 1.5,
    'sea' : 0.6,
    'iwt' : 0.45
}

co2_per_km = {
    'road': 150,
    'rail': 30,
    'sea': 50,
    'iwt': 30
}

# Transfer cost at MMLP (₹ per car)
transfer_cost = {
    ('road', 'rail'): 600,
    ('road', 'sea'): 800,
    ('road', 'iwt'): 600,
    ('rail', 'road'): 600,
    ('rail', 'sea'): 700,
    ('rail', 'iwt'): 600,
    ('sea', 'road'): 800,
    ('sea', 'rail'): 700,
    ('sea', 'iwt'): 700,
    ('iwt', 'road'): 600,
    ('iwt', 'rail'): 600,
    ('iwt', 'sea'): 700
}


transit_speeds = {
    'road': 50,    # km/hour
    'rail': 30,    # km/hour
    'sea': 25,     # km/hour
    'iwt': 15      # km/hour
}

transfer_times = {
    ('road', 'rail'): 4,
    ('road', 'sea'): 8,
    ('road', 'iwt'): 6,
    ('rail', 'road'): 4,
    ('rail', 'sea'): 6,
    ('rail', 'iwt'): 5,
    ('sea', 'road'): 8,
    ('sea', 'rail'): 6,
    ('sea', 'iwt'): 7,
    ('iwt', 'road'): 6,
    ('iwt', 'rail'): 5,
    ('iwt', 'sea'): 7
}


cost_per_tonne_km = {
    'road': 3.67,   # ₹55 for 15-tonne truck ÷ 15 tonnes
    'rail': 1.0,    # ₹22.5 for 22.5-tonne wagon ÷ 22.5
    'sea': 0.4,     # ₹90 for 225-tonne ship ÷ 225
    'iwt': 0.3      # ₹45 for 150-tonne barge ÷ 150
}

# CO₂ per TONNE-kilometer (g/tonne-km)
co2_per_tonne_km = {
    'road': 100,    # 1500g for 15-tonne truck ÷ 15
    'rail': 20,     # 450g for 22.5-tonne wagon ÷ 22.5
    'sea': 33.3,    # 7500g for 225-tonne ship ÷ 225
    'iwt': 20       # 3000g for 150-tonne barge ÷ 150
}

# Vehicle capacity in TONNES (for vehicle calculation)
vehicle_capacity_tonnes = {
    'road': 15,
    'rail': 22.5,
    'sea': 225,
    'iwt': 150
}

# ========== VEHICLE TYPES ==========
vehicle_types = {
    # ROAD VEHICLES
    'light_truck': {
        'name': 'Light Truck',
        'mode': 'road',
        'capacity_tonnes': 7.5,
        'cost_per_km': 35,
        'co2_per_km': 90,
        'speed': 45,
        'cost_per_tonne_km': 35 / 7.5,  # ₹4.67
        'co2_per_tonne_km': 90 / 7.5,   # 12g
        'emoji': '🚛'
    },
    'standard_truck': {
        'name': 'Standard Truck',
        'mode': 'road',
        'capacity_tonnes': 15,
        'cost_per_km': 55,
        'co2_per_km': 150,
        'speed': 50,
        'cost_per_tonne_km': 55 / 15,   # ₹3.67
        'co2_per_tonne_km': 150 / 15,   # 10g
        'emoji': '🚛'
    },
    'heavy_truck': {
        'name': 'Heavy Truck',
        'mode': 'road',
        'capacity_tonnes': 25,
        'cost_per_km': 80,
        'co2_per_km': 220,
        'speed': 45,
        'cost_per_tonne_km': 80 / 25,   # ₹3.20
        'co2_per_tonne_km': 220 / 25,   # 8.8g
        'emoji': '🚛'
    },
    
    # RAIL VEHICLES
    'standard_wagon': {
        'name': 'Standard Wagon',
        'mode': 'rail',
        'capacity_tonnes': 22.5,
        'cost_per_km': 22.5,
        'co2_per_km': 30,
        'speed': 30,
        'cost_per_tonne_km': 22.5 / 22.5,  # ₹1.00
        'co2_per_tonne_km': 30 / 22.5,     # 1.33g
        'emoji': '🚂'
    },
    'double_stack': {
        'name': 'Double-Stack Wagon',
        'mode': 'rail',
        'capacity_tonnes': 45,
        'cost_per_km': 35,
        'co2_per_km': 45,
        'speed': 28,
        'cost_per_tonne_km': 35 / 45,      # ₹0.78
        'co2_per_tonne_km': 45 / 45,       # 1.0g
        'emoji': '🚂'
    },
    
    # SEA VEHICLES
    'coastal_roro': {
        'name': 'Coastal Ro-Ro',
        'mode': 'sea',
        'capacity_tonnes': 225,
        'cost_per_km': 90,
        'co2_per_km': 50,
        'speed': 25,
        'cost_per_tonne_km': 90 / 225,     # ₹0.40
        'co2_per_tonne_km': 50 / 225,      # 0.22g
        'emoji': '🚢'
    },
    'small_roro': {
        'name': 'Small Ro-Ro',
        'mode': 'sea',
        'capacity_tonnes': 150,
        'cost_per_km': 70,
        'co2_per_km': 40,
        'speed': 22,
        'cost_per_tonne_km': 70 / 150,     # ₹0.47
        'co2_per_tonne_km': 40 / 150,      # 0.27g
        'emoji': '🚢'
    },
    
    # IWT VEHICLES
    'iwt_barge': {
        'name': 'IWT Barge',
        'mode': 'iwt',
        'capacity_tonnes': 150,
        'cost_per_km': 45,
        'co2_per_km': 30,
        'speed': 15,
        'cost_per_tonne_km': 45 / 150,     # ₹0.30
        'co2_per_tonne_km': 30 / 150,      # 0.2g
        'emoji': '🛶'
    }
}

# Default vehicle for each mode (if user doesn't specify)
default_vehicles = {
    'road': 'standard_truck',
    'rail': 'standard_wagon',
    'sea': 'coastal_roro',
    'iwt': 'iwt_barge'
}


# For backward compatibility, keep old names but point to new values
cost_per_km = cost_per_tonne_km
co2_per_km = co2_per_tonne_km


mmlps = ['Nagpur', 'Bengaluru', 'Jogighopa', 'Chennai', 'Delhi']

def build_layered_graph(G, mmlps):
    
    L = nx.DiGraph()  # Layered graph
    
    # Add nodes with layer information
    for node in G.nodes():
        for mode in ['road', 'rail', 'sea', 'iwt']:
            L.add_node((node, mode))
    
    # Add intra-layer edges (travel within same mode)
    for u, v, data in G.edges(data=True):
        mode = data.get('mode')
        distance = data.get('distance')
        
        if mode and distance:
            # Calculate travel time
            travel_time = distance / transit_speeds.get(mode, 30)
            
            L.add_edge((u, mode), (v, mode),
                       weight=distance,
                       cost=distance * cost_per_km[mode],
                       co2=distance * co2_per_km[mode],
                       time=travel_time,  # NEW: Add time
                       type='travel')
    
    # Add inter-layer edges (mode transfers at MMLPs)
    for mmlp in mmlps:
        for mode1 in ['road', 'rail', 'sea', 'iwt']:
            for mode2 in ['road', 'rail', 'sea', 'iwt']:
                if mode1 != mode2:
                    transfer_cost_val = transfer_cost.get((mode1, mode2), 1000)
                    transfer_time_val = transfer_times.get((mode1, mode2), 6)  
                    
                    L.add_edge((mmlp, mode1), (mmlp, mode2),
                               weight=0,
                               cost=transfer_cost_val,
                               co2=0,
                               time=transfer_time_val,  # NEW: Add transfer time
                               type='transfer')
    
    return L

# Build the layered graph
mmlps = ['Nagpur', 'Bengaluru', 'Jogighopa', 'Chennai', 'Delhi']


L = build_layered_graph(G, mmlps)
print(f"Layered graph has {L.number_of_nodes()} nodes and {L.number_of_edges()} edges")


def find_optimal_route(G, start, end, mmlps, objective='cost', weights=None):
    L = build_layered_graph(G, mmlps)
    
    # Determine weight attribute
    if objective == 'cost':
        weight_attr = 'cost'
    elif objective == 'co2':
        weight_attr = 'co2'
    elif objective == 'time':
        weight_attr = 'time'
    elif objective == 'balanced':
        weight_attr = 'balanced'
    else:
        raise ValueError(f"Unknown objective: {objective}")
    
    # Find valid start nodes (only modes that exist at origin)
    start_nodes = []
    for mode in ['road', 'rail', 'sea', 'iwt']:
        # Check if origin has outgoing edges in this mode
        has_outgoing = any(
            data.get('mode') == mode 
            for _, _, data in G.edges(start, data=True)
        )
        if has_outgoing:
            start_nodes.append((start, mode))
    
    # If no specific modes found, use road as default
    if not start_nodes:
        start_nodes = [(start, 'road')]
    
    end_nodes = [(end, mode) for mode in ['road', 'rail', 'sea', 'iwt']]
    
    best_path = None
    best_value = float('inf')
    best_cost = float('inf')
    best_co2 = float('inf')
    best_time = float('inf')
    best_distance = 0
    
    for start_node in start_nodes:
        for end_node in end_nodes:
            try:
                # Find shortest path
                path = nx.shortest_path(L, source=start_node, target=end_node, weight=weight_attr)
                
                # CRITICAL FIX: Check if first edge is a transfer
                u, v = path[0], path[1]
                first_edge = L.get_edge_data(u, v)
                
                if first_edge['type'] == 'transfer':
                    # This path starts with a transfer - penalize it heavily
                    # Either skip it entirely or give it a massive penalty
                    continue  # Skip this path entirely

                u_last, v_last = path[-2], path[-1]
                last_edge = L.get_edge_data(u_last, v_last)
                if last_edge['type'] == 'transfer':
                    continue  # Skip paths that end with transfer


                has_bad_transfer = False
                for i in range(len(path)-2):
                    u, v = path[i], path[i+1]
                    edge = L.get_edge_data(u, v)
                    next_edge = L.get_edge_data(path[i+1], path[i+2])
                    
                    # Two transfers in a row? Skip
                    if edge['type'] == 'transfer' and next_edge['type'] == 'transfer':
                        has_bad_transfer = True
                        break
                
                if has_bad_transfer:
                    continue
                
                # Calculate all metrics
                total_cost = 0
                total_co2 = 0
                total_time = 0
                total_distance = 0
                
                for i in range(len(path)-1):
                    u, v = path[i], path[i+1]
                    edge_data = L.get_edge_data(u, v)
                    
                    total_cost += edge_data.get('cost', 0)
                    total_co2 += edge_data.get('co2', 0)
                    total_time += edge_data.get('time', 0)
                    if edge_data.get('type') == 'travel':
                        total_distance += edge_data.get('weight', 0)
                
                # Calculate value based on objective
                if objective == 'cost':
                    current_value = total_cost
                elif objective == 'co2':
                    current_value = total_co2
                elif objective == 'time':
                    current_value = total_time
                elif objective == 'balanced':
                    # Default weights if not provided
                    if weights is None:
                        weights = {'cost': 0.34, 'co2': 0.33, 'time': 0.33}
                    
                    # NORMALIZATION: Find min/max for each metric across ALL paths
                    # But since we can't know all paths, use reasonable reference values
                    REF_COST = 20000      # ₹20,000 per tonne (typical long route)
                    REF_CO2 = 2000000     # 2,000,000g CO₂ (2 tonnes)
                    REF_TIME = 120        # 120 hours (5 days)
                    
                    # Normalized scores (0-1 scale, lower is better)
                    cost_score = total_cost / REF_COST
                    co2_score = total_co2 / REF_CO2
                    time_score = total_time / REF_TIME
                    
                    # Clip to reasonable range
                    cost_score = min(cost_score, 2.0)
                    co2_score = min(co2_score, 2.0)
                    time_score = min(time_score, 2.0)
                    
                    # Weighted combination
                    current_value = (
                        weights['cost'] * cost_score +
                        weights['co2'] * co2_score +
                        weights['time'] * time_score
                    )
                    
                    # DEBUG: Print to verify weights are working
                    print(f"   Weights: C:{weights['cost']:.2f}, CO2:{weights['co2']:.2f}, T:{weights['time']:.2f}")
                    print(f"   Scores: C:{cost_score:.3f}, CO2:{co2_score:.3f}, T:{time_score:.3f}")
                    print(f"   Weighted: {current_value:.3f}")
                
                if current_value < best_value:
                    best_value = current_value
                    best_path = path
                    best_cost = total_cost
                    best_co2 = total_co2
                    best_time = total_time
                    best_distance = total_distance
                    
            except nx.NetworkXNoPath:
                continue
    
    return best_path, best_cost, best_co2, best_time, best_distance
  
def decode_layered_path(path):
    
    readable = []
    
    for i in range(len(path)-1):
        (city1, mode1), (city2, mode2) = path[i], path[i+1]
        
        if city1 == city2:
            # Transfer at same city
            readable.append(f"Transfer: {mode1} → {mode2} at {city1}")
        else:
            # Travel between different cities
            readable.append(f"Travel: {city1} → {city2} by {mode1}")
    
    return readable

def compare_with_road(G, start, end, opt_cost, opt_co2):
    """Compare optimal route with all-road baseline"""
    result = shortest_road_path(G, start, end)
    
    if result is None or result[0] is None:
        print(f"   No road path available for comparison")
        return None, None, None, None, None, None
    
    road_path, road_dist, edges_road = result  # Unpack all three returned values
    
    # Check if road_dist is valid
    if road_dist is None or road_dist <= 0:
        print(f"   Invalid road distance: {road_dist}")
        return None, None, None, None, None, None
    
    road_cost = road_dist * cost_per_km['road']
    road_co2 = road_dist * co2_per_km['road']
    
    savings = road_cost - opt_cost
    savings_pct = (savings / road_cost) * 100 if road_cost > 0 else 0
    
    co2_reduction = road_co2 - opt_co2
    co2_reduction_pct = (co2_reduction / road_co2) * 100 if road_co2 > 0 else 0
    
    return road_cost, road_co2, savings, savings_pct, co2_reduction, co2_reduction_pct

def calculate_shipment_optimized(tonnes, origin, destination, mmlps, 
                                 objective='cost', weights=None,selected_vehicles= None):
    """
    Calculate optimal shipping for ANY shipment size
    - amount: number of cars OR tonnes
    - unit: 'cars' or 'tonnes'
    - objective: 'cost', 'co2', 'time', 'balanced'
    - weights: for balanced optimization
    """
    if selected_vehicles is None:
        selected_vehicles = {}
        
    shipment_tonnes = tonnes

    global cost_per_km, co2_per_km, transit_speeds, vehicle_capacity_tonnes

       # Save originals
    orig_cost = cost_per_km.copy()
    orig_co2 = co2_per_km.copy()
    orig_speed = transit_speeds.copy()
    orig_capacity = vehicle_capacity_tonnes.copy()
    
    # Apply selected vehicles
    vehicles_used = {}
    for mode in ['road', 'rail', 'sea', 'iwt']:
        vehicle_key = selected_vehicles.get(mode, default_vehicles[mode])
        vehicle = vehicle_types[vehicle_key]
        
        # Override with this vehicle's economics
        cost_per_km[mode] = vehicle['cost_per_tonne_km']
        co2_per_km[mode] = vehicle['co2_per_tonne_km']
        transit_speeds[mode] = vehicle['speed']
        vehicle_capacity_tonnes[mode] = vehicle['capacity_tonnes']
        
        vehicles_used[mode] = {
            'type': vehicle_key,
            'name': vehicle['name'],
            'capacity': vehicle['capacity_tonnes'],
            'emoji': vehicle['emoji'] }
        

    # 1. Find the optimal path
    path, opt_cost_per_tonne, opt_co2_per_tonne, opt_time, opt_dist = find_optimal_route(
        G, origin, destination, mmlps, objective, weights)
    
    if not path:
        print(f"❌ No path found from {origin} to {destination}")
        return None
    
    # 2. Decode the path for readable output
    readable_path = decode_layered_path(path)
    
    # 3. Scale up for number of cars
    total_cost = shipment_tonnes * opt_cost_per_tonne
    total_co2 = shipment_tonnes * opt_co2_per_tonne
    total_time = opt_time
    
    
    # Track vehicles per mode segment
    vehicle_summary = {}
    segment_vehicles = []
    L = build_layered_graph(G, mmlps)
    
    leg_details = []  # Store leg details for dashboard
    
    print("\n" + "="*70)
    print(f"📦 SHIPMENT DETAILS: {shipment_tonnes} tonnes from {origin} to {destination}")
    print("="*70)
    
    print("\n📍 ROUTE BREAKDOWN:")
    leg_number = 1
    
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        edge_data = L.get_edge_data(u, v)
        
        if edge_data['type'] == 'travel':
            mode = u[1]  # (city, mode) tuple
            from_city = u[0]
            to_city = v[0]
            distance = edge_data.get('weight', 0)
            
            # Calculate vehicles needed for this segment
            if mode in vehicle_capacity_tonnes:
                vehicle_info = vehicles_used.get(mode, {})
                vehicles_needed = shipment_tonnes / vehicle_capacity_tonnes[mode]
                vehicles_needed = int(vehicles_needed) + (vehicles_needed % 1 > 0)
                
                if mode not in vehicle_summary:
                    vehicle_summary[mode] = 0
                vehicle_summary[mode] += vehicles_needed
                
                segment_vehicles.append({
                    'leg': leg_number,
                    'from': from_city,
                    'to': to_city,
                    'mode': mode,
                    'vehicles': vehicles_needed,
                    'capacity': vehicle_capacity_tonnes[mode],
                    'distance': distance
                })
                
                # Store for dashboard
                leg_details.append({
                    'type': 'travel',
                    'number': leg_number,
                    'from': from_city,
                    'to': to_city,
                    'mode': mode,
                    'distance': distance,
                    'vehicles_needed': vehicles_needed,
                    'capacity': vehicle_capacity_tonnes[mode],
                    'cost' : distance*cost_per_km[mode]* tonnes,
                    'co2' : distance * co2_per_km[mode] * tonnes / 1000,
                    'time' : distance/transit_speeds[mode]
                })
            
            # Print travel leg
            print(f"\n{leg_number}. {vehicle_info.get('emoji', '🚚')} Travel: {from_city} → {to_city} by {mode}")
            print(f"   Vehicle: {vehicle_info.get('name', mode)} ({vehicle_info.get('capacity', '?')}t capacity)")
            print(f"   Distance: {distance} km")
            print(f"   Vehicles required: {vehicles_needed} × {mode}")
            print(f"   Cost: ₹{distance * cost_per_km[mode] * tonnes:,.0f}")
            print(f"   CO₂: {distance * co2_per_km[mode] * tonnes / 1000:.1f} kg")
            print(f"   Time: {distance / transit_speeds[mode]:.1f} hours")
            leg_number += 1
            
        elif edge_data['type'] == 'transfer':
            mode_from = u[1]
            mode_to = v[1]
            city = u[0]
            transfer_cost = edge_data.get('cost', 0)
            transfer_time = transfer_times.get((mode_from, mode_to))
            
            # Store for dashboard
            leg_details.append({
                'type': 'transfer',
                'city': city,
                'from_mode': mode_from,
                'to_mode': mode_to,
                'cost_per_tonne': transfer_cost,
                'total_cost': transfer_cost * shipment_tonnes,
                'transfer_time': transfer_time
            })
            
            # Print transfer leg
            print(f"   ⚡ TRANSFER at {city}:")
            print(f"   {mode_from.upper()} → {mode_to.upper()}")
            print(f"   Transfer cost per tonne: ₹{transfer_cost:.2f}")
            print(f"   Total transfer cost: ₹{transfer_cost * shipment_tonnes:.2f}")
            print()
    
    # 5. Print summary
    print("📊 SHIPMENT SUMMARY:")
    print(f"   • Total tonnes: {shipment_tonnes}")
    print(f"   • Cost per tonne: ${opt_cost_per_tonne:.2f}")
    print(f"   • CO₂ per tonne: {opt_co2_per_tonne/1000:.1f}Kg")
    print(f"   • Total distance: {opt_dist:.0f} km")
    print(f"   • Total cost: ${total_cost:.2f}")
    print(f"   • Total CO2: {total_co2/1000:.1f} kg")
    
    print("\n🚚 VEHICLE REQUIREMENTS:")
    for mode, count in vehicle_summary.items():
        capacity = vehicle_capacity_tonnes[mode]
        print(f"   • {mode.upper()}: {count} vehicles (capacity: {vehicle_capacity_tonnes} tonnes each)")
    
    # 6. Compare with road-only
    print("\n🆚 COMPARISON WITH ROAD-ONLY TRANSPORT:")
    road_comparison = compare_with_road(G, origin, destination, opt_cost_per_tonne, opt_co2_per_tonne)
    
    # Initialize road comparison variables
    road_cost_per_tonne = 0
    road_co2_per_tonne = 0
    savings = 0
    savings_pct = 0
    co2_reduction = 0
    co2_reduction_pct = 0
    total_road_cost = 0
    total_road_co2 = 0
    
    if road_comparison and road_comparison[0] is not None:
        road_cost_per_tonne, road_co2_per_tonne, savings, savings_pct, co2_reduction, co2_reduction_pct = road_comparison
        
        total_road_cost = shipment_tonnes * road_cost_per_tonne
        total_road_co2 = shipment_tonnes * road_co2_per_tonne
        
        print(f"   • Road-only cost per tonne: ₹{road_cost_per_tonne:.2f}")
        print(f"   • Road-only total cost: ₹{total_road_cost:.2f}")
        print(f"   • Multi-modal savings: ₹{total_road_cost - total_cost:.2f} ({savings_pct:.1f}%)")
        print(f"   • CO₂ reduction: {(total_road_co2 - total_co2)/1000:.1f} kg ({co2_reduction_pct:.1f}%)")
    else:
        print("   • No road comparison available")
    
    print("="*70 + "\n")
    
    # 7. Return comprehensive result dictionary for dashboard
    return {
        'optimal_path': readable_path,
        'layered_path': path,  # Keep layered path for calculations
        'leg_details': leg_details,  # Detailed leg information
        'cost_per_tonne': opt_cost_per_tonne,
        'total_cost': total_cost,
        'co2_per_tonne': opt_co2_per_tonne,
        'total_co2': total_co2,
        'distance': opt_dist,
        'vehicles_needed': vehicle_summary,
        'vehicles_used': vehicles_used,
        'selected_vehicles': selected_vehicles,
        'shipment_size': shipment_tonnes,
        'origin': origin,
        'destination': destination,
        'tonnes': shipment_tonnes,  # Add this line
        'shipment_tonnes': shipment_tonnes,  # And this for backward compatibility
        # Road comparison data
        'road_cost_per_tonne': road_cost_per_tonne,
        'road_co2_per_tonne': road_co2_per_tonne,
        'road_cost': total_road_cost,
        'road_co2': total_road_co2,
        'total_time_hours': total_time,
        'total_time_days': total_time / 24,
        'savings': total_road_cost - total_cost,
        'savings_pct': savings_pct,
        'co2_reduction': total_road_co2 - total_co2,
        'co2_reduction_pct': co2_reduction_pct,
        'vehicle_capacities_tonnes': vehicle_capacity_tonnes,
        # MMLPs used
        'mmlps_used': [leg['city'] for leg in leg_details if leg['type'] == 'transfer']
    }



# test_vehicles.py
print("\n" + "="*60)
print(transfer_times.get(('sea','rail')))
print("🧪 TESTING VEHICLE SELECTION")
print("="*60)

# Test 1: Default vehicles
print("\n📦 DEFAULT VEHICLES (Standard Truck + Standard Wagon)")
result1 = calculate_shipment_optimized(
    tonnes=100,
    origin='Delhi',
    destination='Chennai',
    mmlps=mmlps,
    objective='cost',
    selected_vehicles=None
)

# Test 2: Premium vehicles
print("\n📦 PREMIUM VEHICLES (Heavy Truck + Double-Stack)")
selected = {
    'road': 'heavy_truck',
    'rail': 'double_stack',
    'sea': 'coastal_roro',
    'iwt': 'iwt_barge'
}
result2 = calculate_shipment_optimized(
    tonnes=100,
    origin='Delhi',
    destination='Chennai',
    mmlps=mmlps,
    objective='cost',
    selected_vehicles=selected
)

# Compare
if result1 and result2:
    print("\n" + "="*60)
    print("📊 COMPARISON")
    print("="*60)
    print(f"{'Metric':<20} {'Default':<15} {'Premium':<15} {'Change':<10}")
    print("-"*60)
    print(f"{'Total Cost':<20} ₹{result1['total_cost']:<14,.0f} ₹{result2['total_cost']:<14,.0f} "
          f"{((result2['total_cost']/result1['total_cost']-1)*100):>+5.1f}%")
    print(f"{'Vehicles (Road)':<20} {result1['vehicles_needed'].get('road',0):<15} "
          f"{result2['vehicles_needed'].get('road',0):<15}")
    print(f"{'Vehicles (Rail)':<20} {result1['vehicles_needed'].get('rail',0):<15} "
          f"{result2['vehicles_needed'].get('rail',0):<15}")


