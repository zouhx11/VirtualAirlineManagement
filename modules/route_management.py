# modules/route_management.py

import sqlite3
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import random

class RouteType(Enum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"
    REGIONAL = "regional"

class DemandLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class Airport:
    """Airport data structure"""
    icao: str
    iata: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    elevation: int  # feet
    runway_length: int  # feet
    hub_size: str  # "small", "medium", "large", "mega"
    landing_fee_base: float  # USD per landing
    gate_cost_per_hour: float  # USD per hour

@dataclass
class RouteData:
    """Route between two airports"""
    id: str
    origin_icao: str
    destination_icao: str
    distance_nm: int
    route_type: RouteType
    base_demand: DemandLevel
    competition_level: int  # 0-10 scale
    seasonal_factor: float  # multiplier for current season
    historical_load_factor: float  # 0-1
    market_fare_economy: float  # USD
    market_fare_business: float  # USD
    created_date: datetime

@dataclass
class RouteAssignment:
    """Aircraft assignment to a route"""
    id: str
    route_id: str
    aircraft_id: str
    frequency_weekly: int
    departure_times: List[str]  # HH:MM format
    fare_economy: float
    fare_business: float
    load_factor_target: float
    start_date: datetime
    end_date: Optional[datetime]
    active: bool

@dataclass
class RoutePerformance:
    """Performance metrics for a route"""
    route_id: str
    month: str  # YYYY-MM
    total_flights: int
    passengers_carried: int
    revenue: float
    operating_costs: float
    profit: float
    average_load_factor: float
    on_time_performance: float

class RouteEconomics:
    """Route economics calculation engine"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
        self.load_airport_data()
        
    def init_database(self):
        """Initialize route management database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Airports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airports (
                icao TEXT PRIMARY KEY,
                iata TEXT NOT NULL,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                country TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                elevation INTEGER NOT NULL,
                runway_length INTEGER NOT NULL,
                hub_size TEXT NOT NULL,
                landing_fee_base REAL NOT NULL,
                gate_cost_per_hour REAL NOT NULL
            )
        ''')
        
        # Check if routes table exists with current schema, if not create with new schema
        cursor.execute("PRAGMA table_info(routes);")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # If the table doesn't have our expected columns, create additional tables
        if 'route_type' not in existing_columns:
            # Create extended route data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS route_extended_data (
                    route_id TEXT PRIMARY KEY,
                    route_type TEXT NOT NULL,
                    base_demand TEXT NOT NULL,
                    seasonal_factor REAL NOT NULL,
                    historical_load_factor REAL NOT NULL,
                    market_fare_business REAL NOT NULL,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            ''')
        
        # Route assignments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_assignments (
                id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                aircraft_id TEXT NOT NULL,
                frequency_weekly INTEGER NOT NULL,
                departure_times TEXT NOT NULL,
                fare_economy REAL NOT NULL,
                fare_business REAL NOT NULL,
                load_factor_target REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                active INTEGER NOT NULL,
                FOREIGN KEY (route_id) REFERENCES routes (id)
            )
        ''')
        
        # Route performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT NOT NULL,
                month TEXT NOT NULL,
                total_flights INTEGER NOT NULL,
                passengers_carried INTEGER NOT NULL,
                revenue REAL NOT NULL,
                operating_costs REAL NOT NULL,
                profit REAL NOT NULL,
                average_load_factor REAL NOT NULL,
                on_time_performance REAL NOT NULL,
                FOREIGN KEY (route_id) REFERENCES routes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_airport_data(self):
        """Load major airport data into the database"""
        major_airports = [
            # US Major Hubs
            Airport("KJFK", "JFK", "John F Kennedy Intl", "New York", "USA", 40.6398, -73.7789, 13, 14511, "mega", 850, 45),
            Airport("KLAX", "LAX", "Los Angeles Intl", "Los Angeles", "USA", 33.9425, -118.4081, 125, 12091, "mega", 780, 42),
            Airport("KORD", "ORD", "Chicago O'Hare Intl", "Chicago", "USA", 41.9742, -87.9073, 672, 13000, "mega", 720, 38),
            Airport("KATL", "ATL", "Hartsfield-Jackson Atlanta Intl", "Atlanta", "USA", 33.6407, -84.4277, 1026, 12390, "mega", 650, 35),
            Airport("KDEN", "DEN", "Denver Intl", "Denver", "USA", 39.8561, -104.6737, 5431, 16000, "large", 580, 32),
            Airport("KMIA", "MIA", "Miami Intl", "Miami", "USA", 25.7959, -80.2870, 8, 13016, "large", 620, 40),
            Airport("KSEA", "SEA", "Seattle-Tacoma Intl", "Seattle", "USA", 47.4502, -122.3088, 433, 11901, "large", 560, 35),
            Airport("KPHX", "PHX", "Phoenix Sky Harbor Intl", "Phoenix", "USA", 33.4373, -112.0078, 1135, 11489, "large", 520, 30),
            
            # International Major Hubs
            Airport("EGLL", "LHR", "London Heathrow", "London", "UK", 51.4700, -0.4543, 83, 12799, "mega", 950, 55),
            Airport("LFPG", "CDG", "Charles de Gaulle", "Paris", "France", 49.0097, 2.5479, 392, 13123, "mega", 820, 48),
            Airport("EDDF", "FRA", "Frankfurt am Main", "Frankfurt", "Germany", 50.0379, 8.5622, 364, 13123, "mega", 780, 45),
            Airport("RJTT", "NRT", "Narita Intl", "Tokyo", "Japan", 35.7653, 140.3864, 141, 13123, "mega", 1200, 60),
            Airport("WSSS", "SIN", "Singapore Changi", "Singapore", "Singapore", 1.3644, 103.9915, 22, 13123, "mega", 650, 38),
            Airport("OMDB", "DXB", "Dubai Intl", "Dubai", "UAE", 25.2532, 55.3657, 62, 13124, "mega", 580, 42),
            
            # Regional Airports
            Airport("KBOS", "BOS", "Boston Logan Intl", "Boston", "USA", 42.3656, -71.0096, 20, 10083, "large", 480, 28),
            Airport("KDCA", "DCA", "Ronald Reagan Washington National", "Washington", "USA", 38.8512, -77.0402, 15, 6869, "medium", 520, 32),
            Airport("KLAS", "LAS", "McCarran Intl", "Las Vegas", "USA", 36.0840, -115.1537, 2181, 14511, "large", 450, 25),
            Airport("KMCO", "MCO", "Orlando Intl", "Orlando", "USA", 28.4312, -81.3081, 96, 12004, "large", 380, 22),
            Airport("KSFO", "SFO", "San Francisco Intl", "San Francisco", "USA", 37.6213, -122.3790, 13, 11870, "large", 680, 38),
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing airports
        cursor.execute("DELETE FROM airports")
        
        for airport in major_airports:
            cursor.execute('''
                INSERT INTO airports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                airport.icao, airport.iata, airport.name, airport.city, airport.country,
                airport.latitude, airport.longitude, airport.elevation, airport.runway_length,
                airport.hub_size, airport.landing_fee_base, airport.gate_cost_per_hour
            ))
        
        conn.commit()
        conn.close()
    
    def calculate_distance(self, origin_icao: str, dest_icao: str) -> int:
        """Calculate great circle distance between two airports in nautical miles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT latitude, longitude FROM airports WHERE icao = ?", (origin_icao,))
        origin = cursor.fetchone()
        cursor.execute("SELECT latitude, longitude FROM airports WHERE icao = ?", (dest_icao,))
        dest = cursor.fetchone()
        
        conn.close()
        
        if not origin or not dest:
            return 0
        
        # Haversine formula
        lat1, lon1 = math.radians(origin[0]), math.radians(origin[1])
        lat2, lon2 = math.radians(dest[0]), math.radians(dest[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in nautical miles
        distance_nm = int(3440.065 * c)
        return distance_nm
    
    def generate_routes(self, airline_hub: str, route_count: int = 50) -> List[RouteData]:
        """Generate realistic routes from airline hub"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT icao FROM airports WHERE icao != ?", (airline_hub,))
        destinations = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        routes = []
        for i, dest in enumerate(destinations[:route_count]):
            distance = self.calculate_distance(airline_hub, dest)
            
            # Determine route characteristics based on distance
            if distance < 500:
                route_type = RouteType.REGIONAL
                base_demand = random.choice([DemandLevel.MEDIUM, DemandLevel.HIGH])
                competition = random.randint(3, 8)
                base_fare = 120 + distance * 0.15
            elif distance < 1500:
                route_type = RouteType.DOMESTIC
                base_demand = random.choice([DemandLevel.MEDIUM, DemandLevel.HIGH, DemandLevel.VERY_HIGH])
                competition = random.randint(2, 6)
                base_fare = 180 + distance * 0.12
            else:
                route_type = RouteType.INTERNATIONAL
                base_demand = random.choice([DemandLevel.LOW, DemandLevel.MEDIUM, DemandLevel.HIGH])
                competition = random.randint(1, 4)
                base_fare = 350 + distance * 0.08
            
            route_id = f"{airline_hub}_{dest}_{i+1}"
            
            route = RouteData(
                id=route_id,
                origin_icao=airline_hub,
                destination_icao=dest,
                distance_nm=distance,
                route_type=route_type,
                base_demand=base_demand,
                competition_level=competition,
                seasonal_factor=random.uniform(0.8, 1.2),
                historical_load_factor=random.uniform(0.65, 0.85),
                market_fare_economy=base_fare,
                market_fare_business=base_fare * 3.5,
                created_date=datetime.now()
            )
            routes.append(route)
        
        return routes
    
    def save_routes(self, routes: List[RouteData]):
        """Save routes to database using existing schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for route in routes:
            # Insert into main routes table (existing schema)
            cursor.execute('''
                INSERT OR REPLACE INTO routes 
                (id, departure_airport, arrival_airport, distance_nm, demand_passengers, 
                 demand_cargo, competition_level, base_ticket_price, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                route.id, route.origin_icao, route.destination_icao, route.distance_nm,
                200,  # default passenger demand
                5.0,  # default cargo demand
                route.competition_level, route.market_fare_economy,
                route.created_date.isoformat()
            ))
            
            # Insert extended data
            cursor.execute('''
                INSERT OR REPLACE INTO route_extended_data 
                (route_id, route_type, base_demand, seasonal_factor, historical_load_factor, market_fare_business)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                route.id, route.route_type.value, route.base_demand.value,
                route.seasonal_factor, route.historical_load_factor, route.market_fare_business
            ))
        
        conn.commit()
        conn.close()
    
    def get_routes(self, origin_icao: str = None) -> List[RouteData]:
        """Get routes, optionally filtered by origin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Join with extended data table
        query = '''
            SELECT r.id, r.departure_airport, r.arrival_airport, r.distance_nm, 
                   r.competition_level, r.base_ticket_price, r.created_date,
                   e.route_type, e.base_demand, e.seasonal_factor, 
                   e.historical_load_factor, e.market_fare_business
            FROM routes r
            LEFT JOIN route_extended_data e ON r.id = e.route_id
        '''
        
        if origin_icao:
            query += " WHERE r.departure_airport = ?"
            cursor.execute(query, (origin_icao,))
        else:
            cursor.execute(query)
        
        rows = cursor.fetchall()
        conn.close()
        
        routes = []
        for row in rows:
            # Handle missing extended data with defaults
            route_type = RouteType(row[7]) if row[7] else RouteType.DOMESTIC
            base_demand = DemandLevel(row[8]) if row[8] else DemandLevel.MEDIUM
            seasonal_factor = row[9] if row[9] else 1.0
            historical_load_factor = row[10] if row[10] else 0.75
            market_fare_business = row[11] if row[11] else row[5] * 3.5
            
            route = RouteData(
                id=row[0], origin_icao=row[1], destination_icao=row[2], distance_nm=row[3],
                route_type=route_type, base_demand=base_demand,
                competition_level=row[4], seasonal_factor=seasonal_factor,
                historical_load_factor=historical_load_factor, market_fare_economy=row[5],
                market_fare_business=market_fare_business, 
                created_date=datetime.fromisoformat(row[6]) if row[6] else datetime.now()
            )
            routes.append(route)
        
        return routes
    
    def calculate_route_revenue(self, route_id: str, aircraft_capacity: int, 
                              frequency_weekly: int, fare_economy: float, 
                              fare_business: float = None, business_ratio: float = 0.15) -> Dict:
        """Calculate potential revenue for a route"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get route data with extended info
        cursor.execute('''
            SELECT r.id, r.departure_airport, r.arrival_airport, r.distance_nm, 
                   r.competition_level, r.base_ticket_price, r.created_date,
                   e.route_type, e.base_demand, e.seasonal_factor, 
                   e.historical_load_factor, e.market_fare_business
            FROM routes r
            LEFT JOIN route_extended_data e ON r.id = e.route_id
            WHERE r.id = ?
        ''', (route_id,))
        route_data = cursor.fetchone()
        conn.close()
        
        if not route_data:
            return {"error": "Route not found"}
        
        # Route characteristics with defaults for missing extended data
        base_demand = DemandLevel(route_data[8]) if route_data[8] else DemandLevel.MEDIUM
        competition = route_data[4]
        market_fare = route_data[5]
        
        # Demand multipliers
        demand_multipliers = {
            DemandLevel.VERY_LOW: 0.3,
            DemandLevel.LOW: 0.5,
            DemandLevel.MEDIUM: 0.7,
            DemandLevel.HIGH: 0.85,
            DemandLevel.VERY_HIGH: 1.0
        }
        
        # Competition impact on load factor
        competition_impact = max(0.4, 1.0 - (competition * 0.08))
        
        # Price sensitivity (lower fares = higher load factor)
        price_sensitivity = market_fare / fare_economy if fare_economy > 0 else 1.0
        price_impact = min(1.2, max(0.6, price_sensitivity))
        
        # Calculate expected load factor
        base_load_factor = 0.75
        expected_load_factor = (base_load_factor * 
                              demand_multipliers[base_demand] * 
                              competition_impact * 
                              price_impact)
        expected_load_factor = min(0.95, max(0.30, expected_load_factor))
        
        # Calculate passengers
        flights_per_month = frequency_weekly * 4.33
        passengers_per_flight = aircraft_capacity * expected_load_factor
        
        if fare_business and business_ratio > 0:
            business_passengers = passengers_per_flight * business_ratio
            economy_passengers = passengers_per_flight * (1 - business_ratio)
            monthly_revenue = ((economy_passengers * fare_economy + 
                              business_passengers * fare_business) * flights_per_month)
        else:
            monthly_revenue = passengers_per_flight * fare_economy * flights_per_month
        
        return {
            "expected_load_factor": expected_load_factor,
            "passengers_per_flight": passengers_per_flight,
            "flights_per_month": flights_per_month,
            "monthly_passengers": passengers_per_flight * flights_per_month,
            "monthly_revenue": monthly_revenue,
            "competition_impact": competition_impact,
            "price_impact": price_impact
        }
    
    def calculate_operating_costs(self, route_id: str, aircraft_spec: Dict, 
                                frequency_weekly: int) -> Dict:
        """Calculate operating costs for a route"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT distance_nm, departure_airport, arrival_airport FROM routes WHERE id = ?", (route_id,))
        route_data = cursor.fetchone()
        
        cursor.execute("SELECT landing_fee_base, gate_cost_per_hour FROM airports WHERE icao IN (?, ?)", 
                      (route_data[1], route_data[2]))
        airport_costs = cursor.fetchall()
        conn.close()
        
        if not route_data or len(airport_costs) < 2:
            return {"error": "Route or airport data not found"}
        
        distance_nm = route_data[0]
        
        # Flight time calculation (including taxi, climb, descent)
        cruise_speed = aircraft_spec.get('cruise_speed', 450)
        flight_time_hours = (distance_nm / cruise_speed) + 0.5  # 30min ground ops
        
        # Fuel costs
        fuel_burn_per_hour = aircraft_spec.get('fuel_burn_per_hour', 800)
        fuel_price_per_gallon = 3.50  # Average jet fuel price
        fuel_cost_per_flight = flight_time_hours * fuel_burn_per_hour * fuel_price_per_gallon
        
        # Crew costs (per flight)
        crew_required = aircraft_spec.get('crew_required', 2)
        crew_cost_per_hour = 250  # Pilot + cabin crew hourly cost
        crew_cost_per_flight = flight_time_hours * crew_cost_per_hour * crew_required
        
        # Airport fees
        origin_landing_fee = airport_costs[0][0]
        dest_landing_fee = airport_costs[1][0] if len(airport_costs) > 1 else airport_costs[0][0]
        origin_gate_cost = airport_costs[0][1] * 2  # 2 hours gate time
        dest_gate_cost = airport_costs[1][1] * 2 if len(airport_costs) > 1 else airport_costs[0][1] * 2
        
        airport_fees_per_flight = origin_landing_fee + dest_landing_fee + origin_gate_cost + dest_gate_cost
        
        # Maintenance costs (per flight hour)
        maintenance_cost_per_hour = aircraft_spec.get('base_price', 100) * 1000000 * 0.02 / 3000  # 2% of aircraft value per 3000 hours
        maintenance_cost_per_flight = flight_time_hours * maintenance_cost_per_hour
        
        # Calculate monthly costs
        flights_per_month = frequency_weekly * 4.33
        
        monthly_costs = {
            "fuel": fuel_cost_per_flight * flights_per_month,
            "crew": crew_cost_per_flight * flights_per_month,
            "airport_fees": airport_fees_per_flight * flights_per_month,
            "maintenance": maintenance_cost_per_flight * flights_per_month,
            "total": (fuel_cost_per_flight + crew_cost_per_flight + 
                     airport_fees_per_flight + maintenance_cost_per_flight) * flights_per_month
        }
        
        return {
            "per_flight": {
                "fuel": fuel_cost_per_flight,
                "crew": crew_cost_per_flight,
                "airport_fees": airport_fees_per_flight,
                "maintenance": maintenance_cost_per_flight,
                "total": fuel_cost_per_flight + crew_cost_per_flight + airport_fees_per_flight + maintenance_cost_per_flight
            },
            "monthly": monthly_costs,
            "flight_time_hours": flight_time_hours
        }
    
    def calculate_route_profitability(self, route_id: str, aircraft_spec: Dict, 
                                    frequency_weekly: int, fare_economy: float, 
                                    fare_business: float = None, business_ratio: float = 0.15) -> Dict:
        """Calculate complete P&L analysis for a route"""
        
        # Get revenue calculation
        revenue_data = self.calculate_route_revenue(
            route_id, aircraft_spec.get('passenger_capacity', 180), 
            frequency_weekly, fare_economy, fare_business, business_ratio
        )
        
        if "error" in revenue_data:
            return revenue_data
        
        # Get operating costs
        cost_data = self.calculate_operating_costs(route_id, aircraft_spec, frequency_weekly)
        
        if "error" in cost_data:
            return cost_data
        
        # Calculate profitability metrics
        monthly_revenue = revenue_data['monthly_revenue']
        monthly_costs = cost_data['monthly']['total']
        monthly_profit = monthly_revenue - monthly_costs
        
        profit_margin = (monthly_profit / monthly_revenue * 100) if monthly_revenue > 0 else 0
        cost_per_passenger = monthly_costs / revenue_data['monthly_passengers'] if revenue_data['monthly_passengers'] > 0 else 0
        revenue_per_passenger = monthly_revenue / revenue_data['monthly_passengers'] if revenue_data['monthly_passengers'] > 0 else 0
        
        # Break-even analysis
        fixed_costs_monthly = cost_data['monthly']['crew'] + cost_data['monthly']['airport_fees']
        variable_cost_per_passenger = (cost_data['monthly']['fuel'] + cost_data['monthly']['maintenance']) / revenue_data['monthly_passengers'] if revenue_data['monthly_passengers'] > 0 else 0
        breakeven_load_factor = fixed_costs_monthly / (revenue_per_passenger * revenue_data['flights_per_month'] * aircraft_spec.get('passenger_capacity', 180) - variable_cost_per_passenger * revenue_data['flights_per_month'] * aircraft_spec.get('passenger_capacity', 180)) if revenue_per_passenger > variable_cost_per_passenger else 1.0
        
        return {
            "revenue": {
                "monthly_revenue": monthly_revenue,
                "revenue_per_passenger": revenue_per_passenger,
                "load_factor": revenue_data['expected_load_factor'],
                "monthly_passengers": revenue_data['monthly_passengers'],
                "flights_per_month": revenue_data['flights_per_month']
            },
            "costs": {
                "monthly_total": monthly_costs,
                "cost_per_passenger": cost_per_passenger,
                "breakdown": cost_data['monthly']
            },
            "profitability": {
                "monthly_profit": monthly_profit,
                "profit_margin": profit_margin,
                "breakeven_load_factor": min(1.0, max(0.0, breakeven_load_factor)),
                "roi_monthly": (monthly_profit / (aircraft_spec.get('base_price', 100) * 1000000 / 12)) * 100 if aircraft_spec.get('base_price', 0) > 0 else 0
            },
            "efficiency": {
                "cost_per_available_seat_mile": (monthly_costs / (aircraft_spec.get('passenger_capacity', 180) * revenue_data['flights_per_month'] * self.get_route_distance(route_id))),
                "revenue_per_available_seat_mile": (monthly_revenue / (aircraft_spec.get('passenger_capacity', 180) * revenue_data['flights_per_month'] * self.get_route_distance(route_id)))
            }
        }
    
    def get_route_distance(self, route_id: str) -> int:
        """Get distance for a route"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT distance_nm FROM routes WHERE id = ?", (route_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def assign_aircraft_to_route(self, route_id: str, aircraft_id: str, 
                               frequency_weekly: int, departure_times: List[str],
                               fare_economy: float, fare_business: float = None,
                               load_factor_target: float = 0.80) -> Tuple[bool, str]:
        """Assign an aircraft to a route"""
        
        # Validate route exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM routes WHERE id = ?", (route_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "Route not found"
        
        # Validate aircraft exists and is available
        cursor.execute("SELECT id FROM fleet WHERE id = ?", (aircraft_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "Aircraft not found"
        
        # Check if aircraft is already assigned
        cursor.execute("SELECT id FROM route_assignments WHERE aircraft_id = ? AND active = 1", (aircraft_id,))
        if cursor.fetchone():
            conn.close()
            return False, "Aircraft is already assigned to another route"
        
        # Create assignment
        assignment_id = f"{route_id}_{aircraft_id}_{datetime.now().strftime('%Y%m%d')}"
        
        cursor.execute('''
            INSERT INTO route_assignments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assignment_id, route_id, aircraft_id, frequency_weekly,
            json.dumps(departure_times), fare_economy, fare_business or 0,
            load_factor_target, datetime.now().isoformat(), None, 1
        ))
        
        # Update aircraft route assignments (optional - for tracking)
        # Note: Using fleet table instead of owned_aircraft
        try:
            cursor.execute("SELECT spec_data FROM fleet WHERE id = ?", (aircraft_id,))
            result = cursor.fetchone()
            if result and result[0]:
                spec_data = json.loads(result[0])
                if 'route_assignments' not in spec_data:
                    spec_data['route_assignments'] = []
                spec_data['route_assignments'].append(route_id)
                cursor.execute("UPDATE fleet SET spec_data = ? WHERE id = ?", 
                              (json.dumps(spec_data), aircraft_id))
        except Exception:
            # If spec_data doesn't exist or is malformed, continue without error
            pass
        
        conn.commit()
        conn.close()
        
        return True, f"Aircraft {aircraft_id} successfully assigned to route {route_id}"
    
    def optimize_aircraft_assignment(self, available_aircraft: List[Dict], 
                                   available_routes: List[str]) -> List[Dict]:
        """Optimize aircraft assignments to maximize profitability"""
        
        optimization_results = []
        
        for aircraft in available_aircraft:
            aircraft_id = aircraft['id']
            aircraft_spec = aircraft['spec']
            best_route = None
            best_profit = -float('inf')
            best_config = None
            
            for route_id in available_routes:
                # Try different frequency configurations
                for frequency in [7, 14, 21]:  # Daily, twice daily, three times daily
                    # Get route market fare as starting point
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT r.base_ticket_price, e.market_fare_business
                        FROM routes r
                        LEFT JOIN route_extended_data e ON r.id = e.route_id
                        WHERE r.id = ?
                    ''', (route_id,))
                    route_fares = cursor.fetchone()
                    conn.close()
                    
                    if not route_fares:
                        continue
                    
                    market_fare_economy = route_fares[0]
                    market_fare_business = route_fares[1] if route_fares[1] else market_fare_economy * 3.5
                    
                    # Try different pricing strategies
                    for price_factor in [0.85, 0.95, 1.05]:  # 15% below, 5% below, 5% above market
                        fare_economy = market_fare_economy * price_factor
                        fare_business = market_fare_business * price_factor
                        
                        profitability = self.calculate_route_profitability(
                            route_id, aircraft_spec, frequency, fare_economy, fare_business
                        )
                        
                        if "error" not in profitability:
                            monthly_profit = profitability['profitability']['monthly_profit']
                            
                            if monthly_profit > best_profit:
                                best_profit = monthly_profit
                                best_route = route_id
                                best_config = {
                                    'frequency_weekly': frequency,
                                    'fare_economy': fare_economy,
                                    'fare_business': fare_business,
                                    'profitability': profitability
                                }
            
            if best_route and best_config:
                optimization_results.append({
                    'aircraft_id': aircraft_id,
                    'recommended_route': best_route,
                    'configuration': best_config,
                    'monthly_profit': best_profit
                })
        
        # Sort by profitability
        optimization_results.sort(key=lambda x: x['monthly_profit'], reverse=True)
        
        return optimization_results
    
    def get_route_assignments(self, aircraft_id: str = None, route_id: str = None) -> List[RouteAssignment]:
        """Get route assignments with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM route_assignments WHERE active = 1"
        params = []
        
        if aircraft_id:
            query += " AND aircraft_id = ?"
            params.append(aircraft_id)
        
        if route_id:
            query += " AND route_id = ?"
            params.append(route_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        assignments = []
        for row in rows:
            assignment = RouteAssignment(
                id=row[0], route_id=row[1], aircraft_id=row[2], frequency_weekly=row[3],
                departure_times=json.loads(row[4]), fare_economy=row[5], fare_business=row[6],
                load_factor_target=row[7], start_date=datetime.fromisoformat(row[8]),
                end_date=datetime.fromisoformat(row[9]) if row[9] else None, active=bool(row[10])
            )
            assignments.append(assignment)
        
        return assignments
    
    def simulate_monthly_performance(self, assignment_id: str) -> RoutePerformance:
        """Simulate route performance for a month"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM route_assignments WHERE id = ?", (assignment_id,))
        assignment_data = cursor.fetchone()
        
        if not assignment_data:
            conn.close()
            return None
        
        route_id = assignment_data[1]
        aircraft_id = assignment_data[2]
        frequency_weekly = assignment_data[3]
        fare_economy = assignment_data[5]
        fare_business = assignment_data[6]
        
        # Get aircraft specs
        cursor.execute("SELECT spec_data FROM owned_aircraft WHERE id = ?", (aircraft_id,))
        aircraft_spec_data = cursor.fetchone()
        conn.close()
        
        if not aircraft_spec_data:
            return None
        
        aircraft_spec = json.loads(aircraft_spec_data[0])
        
        # Calculate performance
        profitability = self.calculate_route_profitability(
            route_id, aircraft_spec, frequency_weekly, fare_economy, fare_business
        )
        
        if "error" in profitability:
            return None
        
        # Add some randomness for realistic simulation
        actual_load_factor = profitability['revenue']['load_factor'] * random.uniform(0.9, 1.1)
        actual_load_factor = min(1.0, max(0.3, actual_load_factor))
        
        on_time_performance = random.uniform(0.75, 0.95)  # 75-95% on-time
        
        actual_passengers = int(profitability['revenue']['monthly_passengers'] * (actual_load_factor / profitability['revenue']['load_factor']))
        actual_revenue = actual_passengers * (fare_economy * 0.85 + fare_business * 0.15)  # Assume 15% business class
        
        current_month = datetime.now().strftime('%Y-%m')
        
        performance = RoutePerformance(
            route_id=route_id,
            month=current_month,
            total_flights=int(profitability['revenue']['flights_per_month']),
            passengers_carried=actual_passengers,
            revenue=actual_revenue,
            operating_costs=profitability['costs']['monthly_total'],
            profit=actual_revenue - profitability['costs']['monthly_total'],
            average_load_factor=actual_load_factor,
            on_time_performance=on_time_performance
        )
        
        return performance

# Example usage
if __name__ == "__main__":
    # Initialize route economics system
    route_system = RouteEconomics("userdata.db")
    
    # Generate routes from JFK hub
    routes = route_system.generate_routes("KJFK", 20)
    route_system.save_routes(routes)
    
    print("=== Route Economics System ===")
    saved_routes = route_system.get_routes("KJFK")
    
    for route in saved_routes[:5]:  # Show first 5 routes
        print(f"\nRoute: {route.origin_icao} → {route.destination_icao}")
        print(f"Distance: {route.distance_nm} nm | Type: {route.route_type.value}")
        print(f"Market Fare: ${route.market_fare_economy:.0f} | Competition: {route.competition_level}/10")
        
        # Example revenue calculation
        revenue_calc = route_system.calculate_route_revenue(
            route.id, 180, 7, route.market_fare_economy * 0.9  # 10% below market
        )
        
        if "error" not in revenue_calc:
            print(f"Expected Load Factor: {revenue_calc['expected_load_factor']:.1%}")
            print(f"Monthly Revenue: ${revenue_calc['monthly_revenue']:,.0f}")