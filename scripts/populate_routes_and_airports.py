#!/usr/bin/env python3
"""
Populate Routes and Expand Airports Database
"""

import sqlite3
import math
import itertools
from datetime import datetime

# Expanded airport database - 63 major world airports
AIRPORTS = {
    # North America
    'KJFK': {'lat': 40.6413, 'lon': -73.7781, 'name': 'John F Kennedy Intl', 'city': 'New York', 'country': 'USA'},
    'KLAX': {'lat': 33.9425, 'lon': -118.4081, 'name': 'Los Angeles Intl', 'city': 'Los Angeles', 'country': 'USA'},
    'KATL': {'lat': 33.6407, 'lon': -84.4277, 'name': 'Atlanta Hartsfield', 'city': 'Atlanta', 'country': 'USA'},
    'KORD': {'lat': 41.9742, 'lon': -87.9073, 'name': 'Chicago O\'Hare', 'city': 'Chicago', 'country': 'USA'},
    'KBOS': {'lat': 42.3656, 'lon': -71.0096, 'name': 'Boston Logan', 'city': 'Boston', 'country': 'USA'},
    'KDCA': {'lat': 38.8512, 'lon': -77.0402, 'name': 'Reagan Washington', 'city': 'Washington DC', 'country': 'USA'},
    'KLAS': {'lat': 36.0840, 'lon': -115.1537, 'name': 'Las Vegas McCarran', 'city': 'Las Vegas', 'country': 'USA'},
    'KMCO': {'lat': 28.4312, 'lon': -81.3081, 'name': 'Orlando Intl', 'city': 'Orlando', 'country': 'USA'},
    'KSFO': {'lat': 37.6213, 'lon': -122.3790, 'name': 'San Francisco Intl', 'city': 'San Francisco', 'country': 'USA'},
    'KIAH': {'lat': 29.9902, 'lon': -95.3368, 'name': 'Houston Intercontinental', 'city': 'Houston', 'country': 'USA'},
    'KPHX': {'lat': 33.4342, 'lon': -112.0116, 'name': 'Phoenix Sky Harbor', 'city': 'Phoenix', 'country': 'USA'},
    'KDEN': {'lat': 39.8561, 'lon': -104.6737, 'name': 'Denver Intl', 'city': 'Denver', 'country': 'USA'},
    'KMIA': {'lat': 25.7931, 'lon': -80.2906, 'name': 'Miami Intl', 'city': 'Miami', 'country': 'USA'},
    'KSEA': {'lat': 47.4502, 'lon': -122.3088, 'name': 'Seattle Tacoma', 'city': 'Seattle', 'country': 'USA'},
    'KDFW': {'lat': 32.8998, 'lon': -97.0403, 'name': 'Dallas Fort Worth', 'city': 'Dallas', 'country': 'USA'},
    'CYYZ': {'lat': 43.6777, 'lon': -79.6248, 'name': 'Toronto Pearson', 'city': 'Toronto', 'country': 'Canada'},
    'CYVR': {'lat': 49.1939, 'lon': -123.1844, 'name': 'Vancouver Intl', 'city': 'Vancouver', 'country': 'Canada'},
    'MMMX': {'lat': 19.4363, 'lon': -99.0721, 'name': 'Mexico City Intl', 'city': 'Mexico City', 'country': 'Mexico'},
    
    # Europe
    'EGLL': {'lat': 51.4700, 'lon': -0.4543, 'name': 'London Heathrow', 'city': 'London', 'country': 'UK'},
    'EDDF': {'lat': 50.0379, 'lon': 8.5622, 'name': 'Frankfurt am Main', 'city': 'Frankfurt', 'country': 'Germany'},
    'LFPG': {'lat': 49.0097, 'lon': 2.5479, 'name': 'Paris Charles de Gaulle', 'city': 'Paris', 'country': 'France'},
    'EHAM': {'lat': 52.3086, 'lon': 4.7639, 'name': 'Amsterdam Schiphol', 'city': 'Amsterdam', 'country': 'Netherlands'},
    'EDDB': {'lat': 52.3667, 'lon': 13.5033, 'name': 'Berlin Brandenburg', 'city': 'Berlin', 'country': 'Germany'},
    'LIRF': {'lat': 41.8003, 'lon': 12.2389, 'name': 'Rome Fiumicino', 'city': 'Rome', 'country': 'Italy'},
    'LEMD': {'lat': 40.4839, 'lon': -3.5680, 'name': 'Madrid Barajas', 'city': 'Madrid', 'country': 'Spain'},
    'EDDM': {'lat': 48.3538, 'lon': 11.7861, 'name': 'Munich Airport', 'city': 'Munich', 'country': 'Germany'},
    'LOWW': {'lat': 48.1103, 'lon': 16.5697, 'name': 'Vienna Intl', 'city': 'Vienna', 'country': 'Austria'},
    'LSZH': {'lat': 47.4647, 'lon': 8.5492, 'name': 'Zurich Airport', 'city': 'Zurich', 'country': 'Switzerland'},
    'EKCH': {'lat': 55.6181, 'lon': 12.6558, 'name': 'Copenhagen Airport', 'city': 'Copenhagen', 'country': 'Denmark'},
    'ESSA': {'lat': 59.6519, 'lon': 17.9186, 'name': 'Stockholm Arlanda', 'city': 'Stockholm', 'country': 'Sweden'},
    'UUEE': {'lat': 55.9736, 'lon': 37.4125, 'name': 'Moscow Sheremetyevo', 'city': 'Moscow', 'country': 'Russia'},
    'EGKK': {'lat': 51.1481, 'lon': -0.1903, 'name': 'London Gatwick', 'city': 'London', 'country': 'UK'},
    'LPPT': {'lat': 38.7813, 'lon': -9.1357, 'name': 'Lisbon Portela', 'city': 'Lisbon', 'country': 'Portugal'},
    
    # Asia-Pacific
    'RJTT': {'lat': 35.7653, 'lon': 140.3864, 'name': 'Tokyo Narita', 'city': 'Tokyo', 'country': 'Japan'},
    'RJBB': {'lat': 34.7848, 'lon': 135.4381, 'name': 'Osaka Kansai', 'city': 'Osaka', 'country': 'Japan'},
    'ZBAA': {'lat': 40.0801, 'lon': 116.5846, 'name': 'Beijing Capital', 'city': 'Beijing', 'country': 'China'},
    'ZSSS': {'lat': 31.1979, 'lon': 121.3364, 'name': 'Shanghai Pudong', 'city': 'Shanghai', 'country': 'China'},
    'VHHH': {'lat': 22.3080, 'lon': 113.9185, 'name': 'Hong Kong Intl', 'city': 'Hong Kong', 'country': 'China'},
    'WSSS': {'lat': 1.3644, 'lon': 103.9915, 'name': 'Singapore Changi', 'city': 'Singapore', 'country': 'Singapore'},
    'VTBS': {'lat': 13.6900, 'lon': 100.7501, 'name': 'Bangkok Suvarnabhumi', 'city': 'Bangkok', 'country': 'Thailand'},
    'RKSI': {'lat': 37.4602, 'lon': 126.4407, 'name': 'Seoul Incheon', 'city': 'Seoul', 'country': 'South Korea'},
    'RJAA': {'lat': 35.5494, 'lon': 139.7798, 'name': 'Tokyo Haneda', 'city': 'Tokyo', 'country': 'Japan'},
    'YSSY': {'lat': -33.9399, 'lon': 151.1753, 'name': 'Sydney Kingsford Smith', 'city': 'Sydney', 'country': 'Australia'},
    'YMML': {'lat': -37.6690, 'lon': 144.8410, 'name': 'Melbourne Tullamarine', 'city': 'Melbourne', 'country': 'Australia'},
    'NZAA': {'lat': -36.9985, 'lon': 174.7872, 'name': 'Auckland Airport', 'city': 'Auckland', 'country': 'New Zealand'},
    'VIDP': {'lat': 28.5562, 'lon': 77.1000, 'name': 'Delhi Indira Gandhi', 'city': 'Delhi', 'country': 'India'},
    'VOMM': {'lat': 13.1979, 'lon': 80.1689, 'name': 'Chennai Airport', 'city': 'Chennai', 'country': 'India'},
    'OPKC': {'lat': 24.9065, 'lon': 67.1609, 'name': 'Karachi Jinnah', 'city': 'Karachi', 'country': 'Pakistan'},
    
    # Middle East
    'OMDB': {'lat': 25.2532, 'lon': 55.3657, 'name': 'Dubai Intl', 'city': 'Dubai', 'country': 'UAE'},
    'OERK': {'lat': 24.9576, 'lon': 46.6988, 'name': 'Riyadh King Khalid', 'city': 'Riyadh', 'country': 'Saudi Arabia'},
    'OTHH': {'lat': 25.2731, 'lon': 51.6081, 'name': 'Doha Hamad', 'city': 'Doha', 'country': 'Qatar'},
    'LTBA': {'lat': 40.9769, 'lon': 28.8146, 'name': 'Istanbul Airport', 'city': 'Istanbul', 'country': 'Turkey'},
    'OIIE': {'lat': 35.4161, 'lon': 51.1522, 'name': 'Tehran Imam Khomeini', 'city': 'Tehran', 'country': 'Iran'},
    'LLBG': {'lat': 32.0114, 'lon': 34.8867, 'name': 'Tel Aviv Ben Gurion', 'city': 'Tel Aviv', 'country': 'Israel'},
    
    # Africa
    'FACT': {'lat': -33.9648, 'lon': 18.6017, 'name': 'Cape Town Intl', 'city': 'Cape Town', 'country': 'South Africa'},
    'FAOR': {'lat': -26.1392, 'lon': 28.2460, 'name': 'Johannesburg OR Tambo', 'city': 'Johannesburg', 'country': 'South Africa'},
    'HECA': {'lat': 30.1219, 'lon': 31.4056, 'name': 'Cairo Intl', 'city': 'Cairo', 'country': 'Egypt'},
    'GMMN': {'lat': 33.3675, 'lon': -7.5898, 'name': 'Casablanca Mohammed V', 'city': 'Casablanca', 'country': 'Morocco'},
    'FLLW': {'lat': -15.3308, 'lon': 28.4526, 'name': 'Lusaka Kenneth Kaunda', 'city': 'Lusaka', 'country': 'Zambia'},
    'HAAB': {'lat': 8.9778, 'lon': 38.7969, 'name': 'Addis Ababa Bole', 'city': 'Addis Ababa', 'country': 'Ethiopia'},
    
    # South America
    'SBGR': {'lat': -23.4356, 'lon': -46.4731, 'name': 'São Paulo Guarulhos', 'city': 'São Paulo', 'country': 'Brazil'},
    'SAEZ': {'lat': -34.8222, 'lon': -58.5358, 'name': 'Buenos Aires Ezeiza', 'city': 'Buenos Aires', 'country': 'Argentina'},
    'SCEL': {'lat': -33.3928, 'lon': -70.7869, 'name': 'Santiago Arturo Benitez', 'city': 'Santiago', 'country': 'Chile'},
    'SKBO': {'lat': 4.7016, 'lon': -74.1469, 'name': 'Bogotá El Dorado', 'city': 'Bogotá', 'country': 'Colombia'},
    'SPJC': {'lat': -12.0219, 'lon': -77.1142, 'name': 'Lima Jorge Chavez', 'city': 'Lima', 'country': 'Peru'},
    'SBBR': {'lat': -15.8711, 'lon': -47.9172, 'name': 'Brasília Intl', 'city': 'Brasília', 'country': 'Brazil'},
}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in nautical miles using Haversine formula"""
    R = 3440.065  # Earth radius in nautical miles
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def create_airports_table(conn):
    """Create and populate airports table"""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM airports")
    
    # Insert airport data with existing schema
    for icao, data in AIRPORTS.items():
        # Generate IATA code (first 3 letters after K/E/R etc.)
        iata = icao[1:4] if len(icao) > 3 else icao[:3]
        
        # Default values for required fields
        elevation = 100  # Default elevation
        runway_length = 10000  # Default runway length
        hub_size = "large" if icao in ['KJFK', 'KLAX', 'EGLL', 'EDDF', 'RJTT', 'OMDB'] else "medium"
        landing_fee = 500 if hub_size == "large" else 300
        gate_cost = 200 if hub_size == "large" else 150
        
        cursor.execute("""
            INSERT INTO airports (icao, iata, name, city, country, latitude, longitude,
                                elevation, runway_length, hub_size, landing_fee_base, gate_cost_per_hour)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (icao, iata, data['name'], data['city'], data['country'], 
              data['lat'], data['lon'], elevation, runway_length, hub_size, landing_fee, gate_cost))
    
    print(f"✅ Added {len(AIRPORTS)} airports to database")

def populate_routes(conn):
    """Generate and populate route combinations"""
    cursor = conn.cursor()
    
    # Clear existing routes
    cursor.execute("DELETE FROM routes")
    
    # Get major hub airports for route generation
    major_hubs = [
        'KJFK', 'KLAX', 'KATL', 'KORD', 'EGLL', 'EDDF', 'LFPG', 'EHAM',
        'RJTT', 'OMDB', 'WSSS', 'VHHH', 'YSSY', 'SBGR', 'FAOR'
    ]
    
    # Regional airports for domestic/short-haul routes
    regional_airports = list(AIRPORTS.keys())
    
    routes_created = 0
    
    # Generate routes between major hubs (long-haul)
    for origin, destination in itertools.combinations(major_hubs, 2):
        if origin in AIRPORTS and destination in AIRPORTS:
            origin_data = AIRPORTS[origin]
            dest_data = AIRPORTS[destination]
            
            distance = calculate_distance(
                origin_data['lat'], origin_data['lon'],
                dest_data['lat'], dest_data['lon']
            )
            
            # Calculate base pricing based on distance
            base_price = max(150, min(800, 150 + (distance * 0.3)))
            
            # Calculate demand based on airports and distance
            demand = max(100, min(500, int(600 - (distance * 0.1))))
            
            # Competition level based on route importance
            competition = 3 if distance > 3000 else 2
            
            route_id = f"{origin}-{destination}"
            
            cursor.execute("""
                INSERT INTO routes (id, departure_airport, arrival_airport, distance_nm,
                                  demand_passengers, demand_cargo, competition_level,
                                  base_ticket_price, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (route_id, origin, destination, int(distance), demand, 
                  round(distance * 0.05, 1), competition, round(base_price, 2),
                  datetime.now().isoformat()))
            
            routes_created += 1
    
    # Generate some regional routes (shorter distances)
    import random
    random.seed(42)  # For consistent results
    
    for _ in range(200):  # Add 200 additional regional routes
        origin, destination = random.sample(regional_airports, 2)
        
        # Skip if route already exists or same airport
        if origin == destination:
            continue
            
        cursor.execute("SELECT COUNT(*) FROM routes WHERE id = ? OR id = ?", 
                      (f"{origin}-{destination}", f"{destination}-{origin}"))
        if cursor.fetchone()[0] > 0:
            continue
        
        origin_data = AIRPORTS[origin]
        dest_data = AIRPORTS[destination]
        
        distance = calculate_distance(
            origin_data['lat'], origin_data['lon'],
            dest_data['lat'], dest_data['lon']
        )
        
        # Skip very long regional routes
        if distance > 4000:
            continue
        
        base_price = max(80, min(600, 80 + (distance * 0.25)))
        demand = max(50, min(300, int(400 - (distance * 0.08))))
        competition = 1 if distance < 1000 else 2
        
        route_id = f"{origin}-{destination}"
        
        cursor.execute("""
            INSERT INTO routes (id, departure_airport, arrival_airport, distance_nm,
                              demand_passengers, demand_cargo, competition_level,
                              base_ticket_price, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (route_id, origin, destination, int(distance), demand, 
              round(distance * 0.03, 1), competition, round(base_price, 2),
              datetime.now().isoformat()))
        
        routes_created += 1
    
    print(f"✅ Created {routes_created} routes")

def main():
    """Main function to populate routes and airports"""
    print("🌍 Populating Routes and Expanding Airports Database")
    print("=" * 50)
    
    # Connect to database
    try:
        conn = sqlite3.connect("userdata.db")
        
        # Create and populate airports
        create_airports_table(conn)
        
        # Generate and populate routes
        populate_routes(conn)
        
        # Commit changes
        conn.commit()
        
        # Verify results
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM airports")
        airport_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM routes")
        route_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Summary:")
        print(f"   Airports: {airport_count}")
        print(f"   Routes: {route_count}")
        print(f"\n✅ Database population completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()