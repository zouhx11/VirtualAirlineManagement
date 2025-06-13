#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.route_management import RouteEconomics
from core.config_manager import ConfigManager

config_manager = ConfigManager()
db_path = config_manager.get_database_path('userdata')
route_economics = RouteEconomics(db_path)

# Test with one of the existing assignments
route_id = 'KJFK_KMCO_9'
aircraft_spec = {
    'passenger_capacity': 180,
    'cruise_speed': 470,
    'fuel_burn_per_hour': 800,
    'crew_required': 2,
    'base_price': 110
}
frequency = 7
fare_economy = 250.0
fare_business = 875.0

print(f'Testing route profitability for {route_id}')
print(f'Aircraft spec: {aircraft_spec}')
print(f'Frequency: {frequency}/week')
print(f'Fares: Economy ${fare_economy}, Business ${fare_business}')
print()

try:
    analysis = route_economics.calculate_route_profitability(
        route_id, aircraft_spec, frequency, fare_economy, fare_business
    )
    
    if 'error' in analysis:
        print(f'ERROR: {analysis["error"]}')
    else:
        print('=== ANALYSIS RESULTS ===')
        print(f'Monthly Revenue: ${analysis["revenue"]["monthly_revenue"]:,.2f}')
        print(f'Monthly Costs: ${analysis["costs"]["monthly_total"]:,.2f}')
        print(f'Monthly Profit: ${analysis["profitability"]["monthly_profit"]:,.2f}')
        print(f'Profit Margin: {analysis["profitability"]["profit_margin"]:.1f}%')
        print(f'Load Factor: {analysis["revenue"]["load_factor"]:.1%}')
        print(f'Monthly Passengers: {analysis["revenue"]["monthly_passengers"]:,.0f}')
        print()
        print('Cost Breakdown:')
        breakdown = analysis['costs']['breakdown']
        for cost_type, amount in breakdown.items():
            if cost_type != 'total':
                print(f'  {cost_type}: ${amount:,.2f}')
        
except Exception as e:
    import traceback
    print(f'EXCEPTION: {e}')
    traceback.print_exc()