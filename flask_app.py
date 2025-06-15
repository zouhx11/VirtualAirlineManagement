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
from modules.ai_competition import AICompetitionManager
from core.config_manager import ConfigManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
config_manager = ConfigManager()
ai_competition = AICompetitionManager("airline_game.db")

# Initialize database if it doesn't exist
def initialize_database_if_needed():
    """Initialize database and config if they don't exist"""
    db_path = config_manager.get_database_path('userdata')
    
    if not os.path.exists(db_path):
        print("🚀 First time setup - initializing database...")
        # Import and run initial setup
        from scripts.initial_setup import main as setup_main
        setup_main()
        print("✅ Database initialized successfully!")
    
    return db_path

# Initialize database and get path    
db_path = initialize_database_if_needed()
route_economics = RouteEconomics(db_path)
aircraft_marketplace = AircraftMarketplace(db_path)

# Time speed multiplier (global setting)
time_speed = 1.0
# Reference time for consistent calculations
reference_time = time.time()  # Fixed reference point

# Load airports from database
def load_airports():
    """Load airports from database"""
    try:
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT icao, name, city, country, latitude, longitude
                FROM airports
                ORDER BY country, city
            """
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            airports = {}
            for row in cursor.fetchall():
                airports[row['icao']] = {
                    'lat': row['latitude'],
                    'lon': row['longitude'], 
                    'name': row['name'],
                    'city': row['city'],
                    'country': row['country']
                }
            return airports
    except Exception as e:
        print(f"Error loading airports: {e}")
        return {}

# Load airports from database
AIRPORTS = load_airports()

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

def calculate_curved_position(lat1, lon1, lat2, lon2, progress):
    """Calculate position along curved 2D route path - matches frontend curve calculation"""
    
    # Calculate distance and direction
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    distance = math.sqrt(delta_lat * delta_lat + delta_lon * delta_lon)
    
    # For very short routes, use straight line
    if distance < 5:
        lat = lat1 + (lat2 - lat1) * progress
        lon = lon1 + (lon2 - lon1) * progress
        return lat, lon
    
    # Calculate curve parameters for 2D map (same as frontend)
    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2
    
    # Curve offset based on distance - smaller for 2D map
    curve_offset = min(distance * 0.15, 15)  # Max 15 degree offset
    
    # Calculate perpendicular direction for curve
    perp_lat = -delta_lon * (curve_offset / distance)
    perp_lon = delta_lat * (curve_offset / distance)
    
    # Control point for curve
    control_lat = mid_lat + perp_lat
    control_lon = mid_lon + perp_lon
    
    # Quadratic Bezier curve formula
    t = progress
    lat = (1 - t) * (1 - t) * lat1 + 2 * (1 - t) * t * control_lat + t * t * lat2
    lon = (1 - t) * (1 - t) * lon1 + 2 * (1 - t) * t * control_lon + t * t * lon2
    
    return lat, lon

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
    """Generate real-time moving flights - ONE AIRCRAFT = ONE FLIGHT AT A TIME"""
    # Use global reference time for consistent calculations
    global reference_time
    real_time = time.time()
    # Calculate accelerated time based on our reference point
    elapsed_real_time = real_time - reference_time
    accelerated_elapsed_time = elapsed_real_time * time_multiplier
    current_time = reference_time + accelerated_elapsed_time
    active_flights = []
    
    for assignment in assignments:
        dep_airport = AIRPORTS.get(assignment['departure_airport'])
        arr_airport = AIRPORTS.get(assignment['arrival_airport'])
        
        if not dep_airport or not arr_airport:
            continue
            
        dep_lat, dep_lon = dep_airport['lat'], dep_airport['lon']
        arr_lat, arr_lon = arr_airport['lat'], arr_airport['lon']
        
        # Calculate flight time based on distance (ULTRA fast game pace)
        distance = math.sqrt((arr_lat - dep_lat)**2 + (arr_lon - dep_lon)**2)
        flight_time_hours = max(0.005, distance * 0.02)  # ULTRA fast - flights in seconds!
        
        # Rest time between flights (visible parking period)
        rest_time_hours = 0.01  # About 36 seconds rest between flights for visible parking
        total_cycle_time = flight_time_hours + rest_time_hours
        
        # Calculate round-trip cycles (continuous operation)
        frequency = assignment['frequency_weekly']
        # One complete round trip = outbound flight + rest + return flight + rest
        round_trip_duration_hours = (flight_time_hours + rest_time_hours) * 2
        
        # Current position in the round-trip cycle
        current_cycle_time = (current_time / 3600) % round_trip_duration_hours  # Convert to hours
        
        # Debug info (reduced frequency to avoid spam)
        if assignment == assignments[0] and int(current_time) % 10 == 0:  # Every 10 seconds only
            print(f"🔍 Debug - Aircraft {assignment['aircraft_id']}: cycle_time={current_cycle_time:.3f}h, flight_time={flight_time_hours:.3f}h, round_trip={round_trip_duration_hours:.3f}h, speed={time_multiplier}x")
        
        # Determine current phase of round trip
        first_leg_end = flight_time_hours  # End of outbound flight
        first_rest_end = first_leg_end + rest_time_hours  # End of first rest
        second_leg_end = first_rest_end + flight_time_hours  # End of return flight
        # second_rest_end = second_leg_end + rest_time_hours  # End of second rest (cycle repeats)
        
        if current_cycle_time < first_leg_end:
            # OUTBOUND FLIGHT: dep_airport → arr_airport
            raw_progress = current_cycle_time / flight_time_hours
            
            # 🛬 SLOW DOWN LANDING: When close to ground (>90%), reduce progress speed by 50%
            if raw_progress >= 0.90:
                # Create slower landing phase - map 0.90-1.0 to 0.90-1.0 but with 50% speed
                landing_phase = (raw_progress - 0.90) / 0.10  # 0.0 to 1.0 during landing
                slowed_landing = landing_phase * 0.5  # Slow down by 50%
                progress = 0.90 + (slowed_landing * 0.10)  # Map back to 0.90-1.0 range
                if progress > 1.0:  # Cap at 100%
                    progress = 1.0
                print(f"🛬 SLOW LANDING: Aircraft {assignment['aircraft_id']} - raw: {raw_progress:.3f} → slowed: {progress:.3f}")
            else:
                progress = raw_progress
                
            # Use curved path calculation for 2D map
            flight_lat, flight_lon = calculate_curved_position(dep_lat, dep_lon, arr_lat, arr_lon, progress)
            
            lat_diff = arr_lat - dep_lat
            lon_diff = arr_lon - dep_lon
            route_direction = f"{assignment['departure_airport']} → {assignment['arrival_airport']}"
            current_dep = assignment['departure_airport']
            current_arr = assignment['arrival_airport']
            is_return_flight = False
            
        elif current_cycle_time < first_rest_end:
            # 🅿️ RESTING AT ARRIVAL AIRPORT - aircraft parked on ground
            flight_lat = arr_lat  # Parked at arrival airport
            flight_lon = arr_lon
            
            lat_diff = 0  # No movement while parked
            lon_diff = 0
            route_direction = f"PARKED at {assignment['arrival_airport']}"
            current_dep = assignment['arrival_airport']  # Currently at arrival airport
            current_arr = assignment['departure_airport']  # Next destination is departure airport  
            is_return_flight = False
            progress = 0  # 0% progress while resting
            
        elif current_cycle_time < second_leg_end:
            # RETURN FLIGHT: arr_airport → dep_airport  
            flight_progress_time = current_cycle_time - first_rest_end
            raw_progress = flight_progress_time / flight_time_hours
            
            # 🛬 SLOW DOWN LANDING: When close to ground (>90%), reduce progress speed by 50%
            if raw_progress >= 0.90:
                # Create slower landing phase - map 0.90-1.0 to 0.90-1.0 but with 50% speed
                landing_phase = (raw_progress - 0.90) / 0.10  # 0.0 to 1.0 during landing
                slowed_landing = landing_phase * 0.5  # Slow down by 50%
                progress = 0.90 + (slowed_landing * 0.10)  # Map back to 0.90-1.0 range
                if progress > 1.0:  # Cap at 100%
                    progress = 1.0
                print(f"🛬 SLOW LANDING: Aircraft {assignment['aircraft_id']} - raw: {raw_progress:.3f} → slowed: {progress:.3f}")
            else:
                progress = raw_progress
                
            # Use curved path calculation for 2D map (return flight: arr -> dep)
            flight_lat, flight_lon = calculate_curved_position(arr_lat, arr_lon, dep_lat, dep_lon, progress)
            
            lat_diff = dep_lat - arr_lat
            lon_diff = dep_lon - arr_lon
            route_direction = f"{assignment['arrival_airport']} → {assignment['departure_airport']}"
            current_dep = assignment['arrival_airport']
            current_arr = assignment['departure_airport']
            is_return_flight = True
            
        else:
            # 🅿️ RESTING AT DEPARTURE AIRPORT - aircraft parked on ground
            flight_lat = dep_lat  # Parked at departure airport
            flight_lon = dep_lon
            
            lat_diff = 0  # No movement while parked
            lon_diff = 0
            route_direction = f"PARKED at {assignment['departure_airport']}"
            current_dep = assignment['departure_airport']  # Currently at departure airport
            current_arr = assignment['arrival_airport']   # Next destination is arrival airport
            is_return_flight = False
            progress = 0  # 0% progress while resting
            
        # Calculate heading for the current flight
        heading = math.degrees(math.atan2(lon_diff, lat_diff))
        if heading < 0:
            heading += 360
        
        # Calculate realistic altitude based on flight phase
        cruise_altitude = 35000  # Cruise altitude in feet
        
        if progress == 0:
            # 🅿️ PARKED PHASE: Aircraft is resting at airport on ground
            altitude = 0  # On the ground at airport
            status = 'parked'
            color = '#FFC107'  # Yellow/gold for parked aircraft
        elif progress <= 0.05:
            # TAKEOFF PHASE: Climb from 0 to cruise altitude
            takeoff_progress = progress / 0.05  # 0 to 1 during takeoff
            altitude = int(takeoff_progress * cruise_altitude)
            status = 'departing'
            color = 'green'
        elif progress >= 0.90:
            # LANDING PHASE: Descend from cruise altitude to 0 (extended phase for better viewing)
            landing_progress = (1.0 - progress) / 0.10  # 1 to 0 during extended landing phase
            altitude = int(landing_progress * cruise_altitude)
            status = 'arriving'
            color = 'orange'
        else:
            # CRUISE PHASE: Maintain cruise altitude
            altitude = cruise_altitude
            status = 'en_route'
            color = 'red'
        
        flight_name = f"Flight {assignment['aircraft_id']}"
        
        active_flights.append({
            'id': f"{assignment['aircraft_id']}",
            'name': flight_name,
            'lat': flight_lat,
            'lon': flight_lon,
            'heading': heading,
            'aircraft_id': assignment['aircraft_id'],
            'route': route_direction,
            'progress': progress * 100,
            'dep_airport': current_dep,
            'arr_airport': current_arr,
            'status': status,
            'color': color,
            'speed': f"{time_multiplier}x",
            'altitude': altitude,  # Realistic altitude based on flight phase
            'altitude_meters': altitude * 0.3048,  # Convert feet to meters for 3D globe
            'ground_speed': 450 + (progress * 50),  # Simulated varying speed
            'is_return_flight': is_return_flight,
            'cycle_time_remaining': round_trip_duration_hours - current_cycle_time,
            'rest_time_remaining': 0,
            'debug_info': {
                'current_cycle_time': current_cycle_time,
                'flight_time_hours': flight_time_hours,
                'round_trip_duration_hours': round_trip_duration_hours,
                'time_multiplier': time_multiplier,
                'phase': 'outbound' if not is_return_flight else 'return'
            }
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

@app.route('/api/owned_aircraft')
def api_owned_aircraft():
    """Get owned aircraft data"""
    try:
        owned_aircraft = aircraft_marketplace.get_owned_aircraft()
        aircraft_data = []
        for aircraft in owned_aircraft:
            aircraft_data.append({
                'id': aircraft.id,
                'model': aircraft.spec.model,
                'registration': aircraft.id,
                'airframeIcao': aircraft.spec.model,
                'location': aircraft.location,
                'condition': aircraft.condition.value,
                'age_years': aircraft.age_years,
                'purchase_price': aircraft.purchase_price,
                'current_value': aircraft.current_value,
                'financing_type': aircraft.financing_type.value,
                'monthly_payment': aircraft.monthly_payment / 1000,  # Convert to thousands
                'status': 'Active'
            })
        return jsonify(aircraft_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    """Purchase aircraft"""
    try:
        data = request.get_json()
        print(f"🛒 Purchase request received: {data}")
        
        aircraft_id = data.get('aircraft_id')
        financing_type = data.get('financing_type', 'CASH')
        
        print(f"🛩️ Attempting to purchase aircraft {aircraft_id} with {financing_type}")
        
        # Check if FinancingType enum value exists
        try:
            financing_enum = FinancingType[financing_type]
        except KeyError:
            return jsonify({
                'success': False,
                'message': f'Invalid financing type: {financing_type}'
            })
        
        success, message, owned = aircraft_marketplace.purchase_aircraft(
            aircraft_id, financing_enum
        )
        
        print(f"💰 Purchase result: success={success}, message='{message}'")
        
        aircraft_data = None
        if owned:
            aircraft_data = {
                'id': owned.id,
                'model': owned.spec.model,
                'condition': owned.condition.value,
                'age_years': owned.age_years,
                'purchase_price': owned.purchase_price,
                'current_value': owned.current_value,
                'financing_type': owned.financing_type.value,
                'monthly_payment': owned.monthly_payment,
                'location': owned.location
            }
        
        return jsonify({
            'success': success,
            'message': message,
            'aircraft': aircraft_data
        })
    except Exception as e:
        print(f"❌ Purchase API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Purchase failed: {str(e)}'
        })

@app.route('/api/sell_aircraft', methods=['POST'])
def api_sell_aircraft():
    """Sell owned aircraft back to market"""
    try:
        data = request.get_json()
        aircraft_id = data.get('aircraft_id')
        
        if not aircraft_id:
            return jsonify({
                'success': False,
                'message': 'Aircraft ID is required'
            })
        
        print(f"💰 Selling aircraft: {aircraft_id}")
        
        # Initialize marketplace
        marketplace = AircraftMarketplace("airline_game.db")
        
        # Attempt to sell aircraft
        success, message, sale_price = marketplace.sell_aircraft(aircraft_id)
        
        return jsonify({
            'success': success,
            'message': message,
            'sale_price': sale_price
        })
        
    except Exception as e:
        print(f"❌ Sell aircraft API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Sale failed: {str(e)}'
        })

@app.route('/api/aircraft_resale_value/<aircraft_id>', methods=['GET'])
def api_aircraft_resale_value(aircraft_id):
    """Get estimated resale value for an aircraft"""
    try:
        print(f"📊 Getting resale value for: {aircraft_id}")
        
        # Initialize marketplace
        marketplace = AircraftMarketplace("airline_game.db")
        
        # Get resale value
        found, current_value, net_proceeds = marketplace.get_aircraft_resale_value(aircraft_id)
        
        if not found:
            return jsonify({
                'success': False,
                'message': 'Aircraft not found'
            })
        
        # Estimate sale price (similar to sell_aircraft logic)
        import random
        depreciation_factor = random.uniform(0.80, 0.90)
        estimated_sale_price = current_value * depreciation_factor
        
        return jsonify({
            'success': True,
            'current_value': current_value,
            'estimated_sale_price': estimated_sale_price,
            'net_proceeds': net_proceeds
        })
        
    except Exception as e:
        print(f"❌ Resale value API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to get resale value: {str(e)}'
        })

@app.route('/api/assign_route', methods=['POST'])
def api_assign_route():
    """Assign aircraft to route with proper validation"""
    try:
        data = request.get_json()
        route_id = data.get('route_id')
        aircraft_id = data.get('aircraft_id')
        frequency = data.get('frequency', 7)
        economy_fare = data.get('economy_fare', 250)
        business_fare = data.get('business_fare', 875)
        
        print(f"🛩️ Route assignment request: Aircraft {aircraft_id} -> Route {route_id}")
        
        with sqlite3.connect(db_path) as conn:
            # Check if aircraft is already assigned to an active route
            check_query = """
                SELECT route_id, departure_airport, arrival_airport 
                FROM route_assignments ra
                JOIN routes r ON ra.route_id = r.id
                WHERE ra.aircraft_id = ? AND ra.active = 1
            """
            existing = conn.execute(check_query, (str(aircraft_id),)).fetchone()
            
            if existing:
                existing_route_id, dep_airport, arr_airport = existing
                return jsonify({
                    'success': False,
                    'message': f'Aircraft is already assigned to route {dep_airport} → {arr_airport}. Remove existing assignment first.'
                })
            
            # Check if this exact assignment already exists (prevent duplicates)
            duplicate_query = """
                SELECT id FROM route_assignments 
                WHERE aircraft_id = ? AND route_id = ? AND active = 1
            """
            duplicate = conn.execute(duplicate_query, (str(aircraft_id), route_id)).fetchone()
            
            if duplicate:
                return jsonify({
                    'success': False,
                    'message': 'This exact route assignment already exists.'
                })
        
        # Simplified frequency handling for fast game pace
        max_frequency = min(frequency, 7)  # Allow up to daily flights
        departure_times = ["08:00"] * max_frequency
        
        success, message = route_economics.assign_aircraft_to_route(
            route_id, str(aircraft_id), max_frequency, departure_times, 
            economy_fare, business_fare
        )
        
        if success:
            message = f"Route assigned successfully! Flying {max_frequency} times per week (with rest periods)."
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        print(f"❌ Route assignment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Assignment failed: {str(e)}'
        })

@app.route('/api/remove_assignment', methods=['POST'])
def api_remove_assignment():
    """Remove aircraft route assignment"""
    try:
        data = request.get_json()
        aircraft_id = data.get('aircraft_id')
        route_id = data.get('route_id')
        
        if not aircraft_id or not route_id:
            return jsonify({
                'success': False,
                'message': 'Aircraft ID and Route ID are required'
            })
        
        with sqlite3.connect(db_path) as conn:
            # Remove the assignment
            query = """
                UPDATE route_assignments 
                SET active = 0 
                WHERE aircraft_id = ? AND route_id = ? AND active = 1
            """
            cursor = conn.execute(query, (str(aircraft_id), route_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': f'Route assignment removed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No active assignment found to remove'
                })
                
    except Exception as e:
        print(f"❌ Remove assignment error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error removing assignment: {str(e)}'
        })

@app.route('/api/cleanup_assignments', methods=['POST'])
def api_cleanup_assignments():
    """Clean up duplicate and invalid route assignments"""
    try:
        with sqlite3.connect(db_path) as conn:
            # Find and remove duplicate assignments (keep only the latest)
            cleanup_query = """
                DELETE FROM route_assignments 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM route_assignments 
                    GROUP BY aircraft_id, route_id, active
                )
            """
            result = conn.execute(cleanup_query)
            duplicates_removed = result.rowcount
            
            # Deactivate assignments for aircraft that don't exist in fleet
            deactivate_query = """
                UPDATE route_assignments 
                SET active = 0 
                WHERE aircraft_id NOT IN (SELECT id FROM fleet) 
                AND active = 1
            """
            result = conn.execute(deactivate_query)
            invalid_deactivated = result.rowcount
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Cleaned up {duplicates_removed} duplicate assignments and deactivated {invalid_deactivated} invalid assignments',
                'duplicates_removed': duplicates_removed,
                'invalid_deactivated': invalid_deactivated
            })
            
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error cleaning up assignments: {str(e)}'
        })

@app.route('/api/sync_aircraft', methods=['POST'])
def api_sync_aircraft():
    """Sync owned aircraft to fleet table for route assignments"""
    try:
        with sqlite3.connect(db_path) as conn:
            # Get owned aircraft
            owned_query = """
                SELECT id, model, location, age_years, current_value 
                FROM owned_aircraft
            """
            owned_aircraft = conn.execute(owned_query).fetchall()
            
            # Clear existing fleet entries (keep only non-marketplace aircraft)
            conn.execute("DELETE FROM fleet WHERE airlineCode = 1")
            
            # Insert owned aircraft into fleet table
            for aircraft in owned_aircraft:
                aircraft_id, model, location, age_years, current_value = aircraft
                
                # Generate registration number from ID
                registration = aircraft_id.replace('_', '-')
                
                # Map model to ICAO code
                model_mapping = {
                    'A320': 'A320',
                    'A321': 'A321', 
                    'A330': 'A330',
                    'A350': 'A350',
                    'B737': 'B737',
                    'B737 MAX 8': 'B38M',
                    'B777': 'B777',
                    'B787': 'B787',
                    'Embraer E175': 'E175',
                    'ATR 72-600': 'AT76'
                }
                
                # Extract base model for mapping
                base_model = model.split(' ')[0]  # Get first part
                if 'B737' in model:
                    icao_code = 'B38M' if 'MAX' in model else 'B737'
                elif 'Embraer' in model:
                    icao_code = 'E175'
                elif 'ATR' in model:
                    icao_code = 'AT76'
                else:
                    icao_code = model_mapping.get(base_model, 'A321')
                
                # Insert into fleet
                fleet_query = """
                    INSERT OR REPLACE INTO fleet 
                    (id, registration, airframeIcao, logLocation, airlineCode, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                
                # Use a sequential ID for fleet
                fleet_id = len([r for r in conn.execute("SELECT id FROM fleet").fetchall()]) + 1
                
                conn.execute(fleet_query, (
                    fleet_id,
                    registration,
                    icao_code,
                    location,
                    1,  # airlineCode
                    'active'
                ))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Synced {len(owned_aircraft)} aircraft to fleet',
                'synced_count': len(owned_aircraft)
            })
            
    except Exception as e:
        print(f"❌ Sync aircraft error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error syncing aircraft: {str(e)}'
        })

@app.route('/api/time_speed', methods=['POST'])
def api_set_time_speed():
    """Set time speed multiplier"""
    global time_speed
    try:
        data = request.get_json()
        new_speed = float(data.get('speed', 1.0))
        
        # Validate speed range (0.05x to 200x)
        if new_speed < 0.05 or new_speed > 200:
            return jsonify({'error': 'Speed must be between 0.05x and 200x'}), 400
            
        time_speed = new_speed
        
        # Broadcast new speed to all clients
        socketio.emit('time_speed_update', {'speed': time_speed})
        
        print(f"⚡ Time speed set to {time_speed}x")
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
        
        # Calculate fleet value from owned aircraft
        fleet_value = 0
        try:
            owned_aircraft = aircraft_marketplace.get_owned_aircraft()
            fleet_value = sum(aircraft.current_value for aircraft in owned_aircraft)
        except:
            fleet_value = 0
        
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
                # Validate assignment structure
                required_fields = ['route_id', 'frequency_weekly', 'fare_economy', 'fare_business']
                if not all(field in assignment for field in required_fields):
                    print(f"Assignment missing required fields: {assignment}")
                    continue
                
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
                
                # Check if analysis returned an error
                if 'error' in analysis:
                    print(f"Route analysis error for {assignment['route_id']}: {analysis['error']}")
                    continue
                
                # Check if analysis has the expected structure
                if 'revenue' not in analysis or 'costs' not in analysis or 'profitability' not in analysis:
                    print(f"Invalid analysis structure for {assignment['route_id']}: {list(analysis.keys())}")
                    continue
                
                route_revenue = analysis['revenue']['monthly_revenue']
                route_costs = analysis['costs']['monthly_total']
                route_profit = analysis['profitability']['monthly_profit']
                
                monthly_revenue += route_revenue
                monthly_costs += route_costs
                
                # Add to cost breakdown
                costs = analysis['costs'].get('breakdown', {})
                cost_breakdown['fuel'] += costs.get('fuel', 0)
                cost_breakdown['crew'] += costs.get('crew', 0)
                cost_breakdown['maintenance'] += costs.get('maintenance', 0)
                cost_breakdown['airport_fees'] += costs.get('airport_fees', 0)
                
                # Get aircraft info for display
                assigned_aircraft = None
                assignment_aircraft_id = assignment.get('aircraft_id')
                
                for ac in aircraft:
                    # Handle potential string/integer mismatch
                    aircraft_id = ac.get('id')
                    if str(aircraft_id) == str(assignment_aircraft_id):
                        assigned_aircraft = ac
                        break
                
                # Extract aircraft type from available fields
                if assigned_aircraft:
                    # Try to get aircraft type from registration or airframeIcao
                    registration = assigned_aircraft.get('registration', '')
                    airframe_icao = assigned_aircraft.get('airframeIcao', '')
                    
                    # Extract model from registration (e.g., "A321-8212" -> "A321")
                    if registration and '-' in registration:
                        aircraft_type = registration.split('-')[0]
                    elif airframe_icao:
                        aircraft_type = airframe_icao
                    else:
                        aircraft_type = f"Aircraft {assigned_aircraft.get('id', 'Unknown')}"
                else:
                    aircraft_type = 'Unassigned'
                
                # Add to route performance
                route_performance.append({
                    'origin': assignment['departure_airport'],
                    'destination': assignment['arrival_airport'],
                    'distance': assignment['distance_nm'],
                    'frequency': assignment['frequency_weekly'] * 4,  # Convert weekly to monthly
                    'aircraft_type': aircraft_type,
                    'revenue': route_revenue,
                    'costs': route_costs,
                    'profit': route_profit,
                    'margin': analysis['profitability']['profit_margin']
                })
                
            except Exception as e:
                print(f"Error calculating route profitability: {e}")
                continue
        
        net_profit = monthly_revenue - monthly_costs
        
        # Fix ROI calculation for airline tycoon game
        # Use a more reasonable base investment (fleet value + operational capital)
        # Instead of total cash, use a more realistic investment base
        if cash_balance > 1000:  # If cash is unrealistically high (like 99 billion)
            # Use fleet size as proxy for investment base (each aircraft ~$100M investment)
            fleet_investment = len(aircraft) * 100  # $100M per aircraft in millions
            base_investment = max(fleet_investment, 100)  # Minimum $100M base
        else:
            base_investment = max(cash_balance, 100)  # Use actual cash if reasonable
        
        # ROI = (Annual Profit / Investment Base) * 100
        annual_profit = net_profit * 12
        roi = (annual_profit / (base_investment * 1000000)) * 100 if base_investment > 0 else 0
        
        return jsonify({
            'cash_balance': cash_balance,
            'fleet_value': fleet_value,
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
            
            # Balanced update frequency - fast but not overwhelming
            if time_speed <= 10:
                update_interval = 1.0  # 1 second for normal speeds
            elif time_speed <= 50:
                update_interval = 0.5  # 0.5 seconds for high speeds  
            else:
                update_interval = 0.2  # 0.2 seconds for ludicrous speeds
            time.sleep(update_interval)
            
        except Exception as e:
            print(f"Error in broadcast thread: {e}")
            time.sleep(5)

@app.route('/api/ai_competition', methods=['GET'])
def api_ai_competition():
    """Get AI competition status and market overview"""
    try:
        # Initialize AI airlines if they don't exist
        if not ai_competition.ai_airlines:
            ai_competition.initialize_ai_airlines(6)
        
        # Simulate AI decisions
        decisions = ai_competition.simulate_ai_decisions()
        
        # Get competition data
        airlines_data = []
        for airline in ai_competition.ai_airlines:
            airlines_data.append({
                'name': airline.name,
                'iata_code': airline.iata_code,
                'strategy': airline.strategy.value,
                'market_share': airline.market_share,
                'reputation': airline.reputation,
                'fleet_size': airline.fleet_size,
                'route_count': airline.route_count,
                'hub_airport': airline.hub_airport
            })
        
        return jsonify({
            'success': True,
            'ai_airlines': airlines_data,
            'recent_decisions': decisions,
            'market_activity': len(decisions)
        })
        
    except Exception as e:
        print(f"❌ AI Competition API error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get AI competition data: {str(e)}'
        })

@app.route('/api/route_competition/<origin>/<destination>', methods=['GET'])
def api_route_competition(origin, destination):
    """Get competition analysis for a specific route"""
    try:
        competition = ai_competition.get_route_competition(origin, destination)
        
        return jsonify({
            'success': True,
            'origin': origin,
            'destination': destination,
            **competition
        })
        
    except Exception as e:
        print(f"❌ Route Competition API error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get route competition: {str(e)}'
        })

if __name__ == '__main__':
    # Start background thread for aircraft updates
    update_thread = threading.Thread(target=broadcast_aircraft_updates, daemon=True)
    update_thread.start()
    
    print("🚀 Starting Flask app with Socket.IO...")
    print("✈️ Aircraft will update in real-time via WebSocket!")
    print("🗺️ No more page refreshes - smooth map updates!")
    
    # Run the app
    socketio.run(app, host='0.0.0.0', port=9999, debug=True, allow_unsafe_werkzeug=True)