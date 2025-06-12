#!/usr/bin/env python3
"""
Regenerate marketplace with our 13 available aircraft models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.aircraft_marketplace import AircraftMarketplace

def main():
    # Initialize marketplace
    marketplace = AircraftMarketplace("userdata.db")
    
    print("🔄 Regenerating marketplace with 13 available aircraft models...")
    
    # Generate market aircraft (this will only use our 13 defined models)
    market_aircraft = marketplace.generate_market_aircraft(50)  # Generate 50 aircraft for variety
    marketplace.save_market_aircraft(market_aircraft)
    
    print(f"✅ Generated {len(market_aircraft)} aircraft for marketplace")
    
    # Show summary of generated aircraft
    aircraft_counts = {}
    for aircraft in market_aircraft:
        model = aircraft.spec.model
        aircraft_counts[model] = aircraft_counts.get(model, 0) + 1
    
    print("\n📊 Aircraft distribution:")
    for model, count in aircraft_counts.items():
        print(f"  {model}: {count} aircraft")
    
    print(f"\n🎯 All aircraft use our 13 available 3D models!")

if __name__ == "__main__":
    main()