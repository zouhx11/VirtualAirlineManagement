#!/usr/bin/env python3
"""
Flask Backend with Socket.IO for Real-Time Aircraft Tracking
No more page refreshes - pure WebSocket updates!
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sqlite3
import json
import time
import math
import threading
from datetime import datetime
import sys
import os

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.route_management import RouteEconomics
from modules.aircraft_marketplace import AircraftMarketplace, AircraftCategory, FinancingType
from core.config_manager import ConfigManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
config_manager = ConfigManager()
db_path = config_manager.get_database_path('userdata')
route_economics = RouteEconomics(db_path)
aircraft_marketplace = AircraftMarketplace(db_path)

# Time speed multiplier (global setting)
time_speed = 1.0

# Airport coordinates
AIRPORTS = {
    'KJFK': {'lat': 40.6413, 'lon': -73.7781, 'name': 'John F Kennedy Intl'},
    'KLAX': {'lat': 33.9425, 'lon': -118.4081, 'name': 'Los Angeles Intl'},
    'EGLL': {'lat': 51.4700, 'lon': -0.4543, 'name': 'London Heathrow'},
    'EDDF': {'lat': 50.0379, 'lon': 8.5622, 'name': 'Frankfurt am Main'},
    'RJTT': {'lat': 35.7653, 'lon': 140.3864, 'name': 'Tokyo Narita'},
    'OMDB': {'lat': 25.2532, 'lon': 55.3657, 'name': 'Dubai Intl'},
    'KATL': {'lat': 33.6407, 'lon': -84.4277, 'name': 'Atlanta Hartsfield'},
    'KORD': {'lat': 41.9742, 'lon': -87.9073, 'name': 'Chicago O\'Hare'},
    'KBOS': {'lat': 42.3656, 'lon': -71.0096, 'name': 'Boston Logan'},
    'KDCA': {'lat': 38.8512, 'lon': -77.0402, 'name': 'Reagan Washington'},
    'KLAS': {'lat': 36.0840, 'lon': -115.1537, 'name': 'Las Vegas McCarran'},
    'KMCO': {'lat': 28.4312, 'lon': -81.3081, 'name': 'Orlando Intl'},
    'KSFO': {'lat': 37.6213, 'lon': -122.3790, 'name': 'San Francisco Intl'},
    'YSSY': {'lat': -33.9399, 'lon': 151.1753, 'name': 'Sydney Kingsford Smith'},
}

def load_aircraft():
    """Load aircraft from database"""
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT id, registration, airframeIcao, logLocation, airlineCode
                FROM fleet 
                WHERE (airlineCode = ? OR airlineCode IS NULL)
                AND registration IS NOT NULL 
                AND airframeIcao IS NOT NULL
            """
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, (1,))  # airline_id = 1
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error loading aircraft: {e}")
        return []

def load_routes():
    """Load routes from database"""
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT id, departure_airport, arrival_airport, distance_nm, base_ticket_price
                FROM routes
                ORDER BY distance_nm
            """
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error loading routes: {e}")
        return []

def load_assignments():
    """Load current route assignments"""
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT ra.aircraft_id, ra.route_id, ra.frequency_weekly, 
                       ra.fare_economy, ra.fare_business, ra.active,
                       r.departure_airport, r.arrival_airport, r.distance_nm
                FROM route_assignments ra
                JOIN routes r ON ra.route_id = r.id
                WHERE ra.active = 1
            """
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error loading assignments: {e}")
        return []

def generate_active_flights(assignments, time_multiplier=1.0):
    """Generate real-time moving flights based on assignments"""
    current_time = time.time() * time_multiplier
    active_flights = []
    
    for assignment in assignments:
        dep_airport = AIRPORTS.get(assignment['departure_airport'])
        arr_airport = AIRPORTS.get(assignment['arrival_airport'])
        
        if not dep_airport or not arr_airport:
            continue
            
        dep_lat, dep_lon = dep_airport['lat'], dep_airport['lon']
        arr_lat, arr_lon = arr_airport['lat'], arr_airport['lon']
        
        # Calculate flight time based on distance
        distance = math.sqrt((arr_lat - dep_lat)**2 + (arr_lon - dep_lon)**2)
        flight_time_hours = (distance * 60) / time_multiplier  # Faster flights with higher speed
        
        # Generate multiple flights per route based on frequency
        flights_per_day = assignment['frequency_weekly'] / 7
        for flight_num in range(int(flights_per_day) + 1):
            # Each flight starts at different times throughout the day
            flight_start_offset = (flight_num * 24 * 60) / flights_per_day  # minutes
            
            # Calculate current flight progress (0-1)
            time_cycle = (current_time + flight_start_offset * 60) % (flight_time_hours * 60)
            progress = (time_cycle / (flight_time_hours * 60)) % 1.0
            
            # Calculate current position
            flight_lat = dep_lat + (arr_lat - dep_lat) * progress
            flight_lon = dep_lon + (arr_lon - dep_lon) * progress
            
            # Calculate heading (bearing)
            lat_diff = arr_lat - dep_lat
            lon_diff = arr_lon - dep_lon
            heading = math.degrees(math.atan2(lon_diff, lat_diff))
            if heading < 0:
                heading += 360
            
            # Determine flight status
            if progress <= 0.05:
                status = 'departing'
                color = 'green'
            elif progress >= 0.95:
                status = 'arriving'
                color = 'orange'
            else:
                status = 'en_route'
                color = 'red'
            
            flight_name = f"Flight {assignment['aircraft_id']}-{flight_num}"
            
            active_flights.append({
                'id': f"{assignment['aircraft_id']}-{flight_num}",
                'name': flight_name,
                'lat': flight_lat,
                'lon': flight_lon,
                'heading': heading,
                'aircraft_id': assignment['aircraft_id'],
                'route': f"{assignment['departure_airport']} → {assignment['arrival_airport']}",
                'progress': progress * 100,
                'dep_airport': assignment['departure_airport'],
                'arr_airport': assignment['arrival_airport'],
                'status': status,
                'color': color,
                'speed': f"{time_multiplier}x",
                'altitude': 35000,  # Simulated
                'ground_speed': 450 + (progress * 50)  # Simulated varying speed
            })
    
    return active_flights

@app.route('/')
def index():
    """Main page with the aircraft tracking map"""
    return render_template('index.html')

@app.route('/api/aircraft')
def api_aircraft():
    """Get all aircraft"""
    aircraft = load_aircraft()
    return jsonify(aircraft)

@app.route('/api/routes')
def api_routes():
    """Get all routes"""
    routes = load_routes()
    return jsonify(routes)

@app.route('/api/assignments')
def api_assignments():
    """Get route assignments"""
    assignments = load_assignments()
    return jsonify(assignments)

@app.route('/api/airports')
def api_airports():
    """Get airport data"""
    return jsonify(AIRPORTS)

@app.route('/api/marketplace')
def api_marketplace():
    """Get aircraft marketplace data"""
    try:
        market_aircraft = aircraft_marketplace.get_market_aircraft()
        aircraft_data = []
        for aircraft in market_aircraft:
            aircraft_data.append({
                'id': aircraft.id,
                'model': aircraft.spec.model,
                'capacity': aircraft.spec.passenger_capacity,
                'range': aircraft.spec.max_range,
                'speed': aircraft.spec.cruise_speed,
                'age': aircraft.age_years,
                'condition': aircraft.condition.value,
                'location': aircraft.location,
                'price': aircraft.asking_price,
                'lease_rate': aircraft.lease_rate_monthly
            })
        return jsonify(aircraft_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    """Purchase aircraft"""
    try:
        data = request.get_json()
        aircraft_id = data.get('aircraft_id')
        financing_type = data.get('financing_type', 'CASH')
        
        success, message, owned = aircraft_marketplace.purchase_aircraft(
            aircraft_id, FinancingType[financing_type]
        )
        
        return jsonify({
            'success': success,
            'message': message,
            'aircraft': owned.__dict__ if owned else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assign_route', methods=['POST'])
def api_assign_route():
    """Assign aircraft to route"""
    try:
        data = request.get_json()
        route_id = data.get('route_id')
        aircraft_id = data.get('aircraft_id')
        frequency = data.get('frequency', 7)
        economy_fare = data.get('economy_fare', 250)
        business_fare = data.get('business_fare', 875)
        
        departure_times = ["08:00"] * min(frequency, 7)
        
        success, message = route_economics.assign_aircraft_to_route(
            route_id, str(aircraft_id), frequency, departure_times, 
            economy_fare, business_fare
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/time_speed', methods=['POST'])
def api_set_time_speed():
    """Set time speed multiplier"""
    global time_speed
    try:
        data = request.get_json()
        new_speed = float(data.get('speed', 1.0))
        time_speed = new_speed
        
        # Broadcast new speed to all clients
        socketio.emit('time_speed_update', {'speed': time_speed})
        
        return jsonify({'success': True, 'speed': time_speed})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/economics')
def api_economics():
    """Get financial overview and economics data"""
    try:
        assignments = load_assignments()
        aircraft = load_aircraft()
        
        # Calculate cash balance
        try:
            cash_balance = aircraft_marketplace.get_current_cash_balance()
        except:
            cash_balance = 100.0
        
        # Calculate monthly financial metrics
        monthly_revenue = 0
        monthly_costs = 0
        route_performance = []
        
        cost_breakdown = {
            'fuel': 0,
            'crew': 0,
            'maintenance': 0,
            'airport_fees': 0
        }
        
        for assignment in assignments:
            try:
                # Simplified route profitability calculation
                aircraft_spec = {
                    'passenger_capacity': 180,
                    'cruise_speed': 470,
                    'fuel_burn_per_hour': 800,
                    'crew_required': 2,
                    'base_price': 110
                }
                
                analysis = route_economics.calculate_route_profitability(
                    assignment['route_id'], aircraft_spec, 
                    assignment['frequency_weekly'], 
                    assignment['fare_economy'], 
                    assignment['fare_business']
                )
                
                route_revenue = analysis['revenue']['monthly_revenue']
                route_costs = analysis['costs']['total_monthly_cost']
                route_profit = analysis['profitability']['monthly_profit']
                
                monthly_revenue += route_revenue
                monthly_costs += route_costs
                
                # Add to cost breakdown
                costs = analysis['costs']['breakdown']
                cost_breakdown['fuel'] += costs.get('fuel', 0)
                cost_breakdown['crew'] += costs.get('crew', 0)
                cost_breakdown['maintenance'] += costs.get('maintenance', 0)
                cost_breakdown['airport_fees'] += costs.get('airport_fees', 0)
                
                # Add to route performance
                route_performance.append({
                    'route': f"{assignment['departure_airport']} → {assignment['arrival_airport']}",
                    'distance': assignment['distance_nm'],
                    'frequency': assignment['frequency_weekly'],
                    'revenue': route_revenue,
                    'costs': route_costs,
                    'profit': route_profit,
                    'margin': analysis['profitability']['profit_margin']
                })
                
            except Exception as e:
                print(f"Error calculating route profitability: {e}")
                continue
        
        net_profit = monthly_revenue - monthly_costs
        roi = (net_profit / max(cash_balance * 1000000, 1)) * 100 if cash_balance > 0 else 0
        
        return jsonify({
            'cash_balance': cash_balance,
            'monthly_revenue': monthly_revenue,
            'monthly_costs': monthly_costs,
            'net_profit': net_profit,
            'roi': roi,
            'cost_breakdown': cost_breakdown,
            'route_performance': route_performance,
            'fleet_size': len(aircraft)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/route_analysis', methods=['POST'])
def api_route_analysis():
    """Analyze route profitability for assignment"""
    try:
        data = request.get_json()
        route_id = data.get('route_id')
        frequency = data.get('frequency', 7)
        economy_fare = data.get('economy_fare', 250)
        business_fare = data.get('business_fare', 875)
        
        # Default aircraft spec
        aircraft_spec = {
            'passenger_capacity': 180,
            'cruise_speed': 470,
            'fuel_burn_per_hour': 800,
            'crew_required': 2,
            'base_price': 110
        }
        
        analysis = route_economics.calculate_route_profitability(
            route_id, aircraft_spec, frequency, economy_fare, business_fare
        )
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    # Send initial data
    emit('time_speed_update', {'speed': time_speed})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

def broadcast_aircraft_updates():
    """Background thread to broadcast aircraft position updates"""
    while True:
        try:
            assignments = load_assignments()
            active_flights = generate_active_flights(assignments, time_speed)
            
            # Broadcast to all connected clients
            socketio.emit('aircraft_update', {
                'flights': active_flights,
                'timestamp': datetime.now().isoformat(),
                'time_speed': time_speed
            })
            
            # Update every 2 seconds for smooth movement
            time.sleep(2)
            
        except Exception as e:
            print(f"Error in broadcast thread: {e}")
            time.sleep(5)

if __name__ == '__main__':
    # Start background thread for aircraft updates
    update_thread = threading.Thread(target=broadcast_aircraft_updates, daemon=True)
    update_thread.start()
    
    print("🚀 Starting Flask app with Socket.IO...")
    print("✈️ Aircraft will update in real-time via WebSocket!")
    print("🗺️ No more page refreshes - smooth map updates!")
    
    # Run the app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)