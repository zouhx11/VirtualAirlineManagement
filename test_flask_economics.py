#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.route_management import RouteEconomics
from modules.aircraft_marketplace import AircraftMarketplace
from core.config_manager import ConfigManager
import sqlite3

config_manager = ConfigManager()
db_path = config_manager.get_database_path('userdata')

# Test the same logic as the Flask /api/economics endpoint
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

# Initialize systems
route_economics = RouteEconomics(db_path)
aircraft_marketplace = AircraftMarketplace(db_path)

print("=== TESTING FLASK ECONOMICS LOGIC ===")

assignments = load_assignments()
aircraft = load_aircraft()

print(f"Found {len(assignments)} assignments")
print(f"Found {len(aircraft)} aircraft")

# Calculate cash balance
try:
    cash_balance = aircraft_marketplace.get_current_cash_balance()
    print(f"Cash balance: ${cash_balance:.2f}M")
except Exception as e:
    print(f"Error getting cash balance: {e}")
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

print("\n=== PROCESSING ASSIGNMENTS ===")
for assignment in assignments:
    try:
        print(f"\nProcessing assignment: Aircraft {assignment['aircraft_id']} on route {assignment['route_id']}")
        
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
        
        if 'error' in analysis:
            print(f"  ERROR: {analysis['error']}")
            continue
        
        route_revenue = analysis['revenue']['monthly_revenue']
        route_costs = analysis['costs']['monthly_total']
        route_profit = analysis['profitability']['monthly_profit']
        
        print(f"  Revenue: ${route_revenue:,.2f}")
        print(f"  Costs: ${route_costs:,.2f}")
        print(f"  Profit: ${route_profit:,.2f}")
        
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
        print(f"Error calculating route profitability for {assignment['route_id']}: {e}")
        import traceback
        traceback.print_exc()
        continue

net_profit = monthly_revenue - monthly_costs
roi = (net_profit / max(cash_balance * 1000000, 1)) * 100 if cash_balance > 0 else 0

print(f"\n=== FINAL RESULTS ===")
print(f"Total Monthly Revenue: ${monthly_revenue:,.2f}")
print(f"Total Monthly Costs: ${monthly_costs:,.2f}")
print(f"Net Profit: ${net_profit:,.2f}")
print(f"ROI: {roi:.2f}%")
print(f"Fleet Size: {len(aircraft)}")

print(f"\nCost Breakdown:")
for cost_type, amount in cost_breakdown.items():
    print(f"  {cost_type}: ${amount:,.2f}")

print(f"\nRoute Performance:")
for route in route_performance:
    print(f"  {route['route']}: ${route['revenue']:,.0f} revenue, ${route['costs']:,.0f} costs, {route['margin']:.1f}% margin")