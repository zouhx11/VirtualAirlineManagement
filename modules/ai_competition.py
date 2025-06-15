# modules/ai_competition.py

import sqlite3
import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import math

class AIStrategy(Enum):
    AGGRESSIVE = "aggressive"  # Low prices, high frequency
    PREMIUM = "premium"       # High prices, good service
    BUDGET = "budget"         # Very low prices, basic service
    BALANCED = "balanced"     # Middle ground approach

class AIPersonality(Enum):
    CAUTIOUS = "cautious"     # Conservative expansion
    AGGRESSIVE = "aggressive" # Rapid expansion
    OPPORTUNISTIC = "opportunistic" # React to player moves
    SPECIALIST = "specialist" # Focus on specific routes/aircraft

@dataclass
class AIAirline:
    """AI-controlled competitor airline"""
    id: str
    name: str
    iata_code: str
    strategy: AIStrategy
    personality: AIPersonality
    cash_balance: float  # millions USD
    fleet_size: int
    hub_airport: str
    market_share: float  # 0.0 to 1.0
    reputation: float    # 0.0 to 1.0
    preferred_aircraft: List[str]  # Aircraft models they prefer
    route_count: int
    monthly_revenue: float
    monthly_costs: float
    last_decision_date: datetime
    
@dataclass
class AIRoute:
    """Route operated by AI airline"""
    id: str
    airline_id: str
    origin: str
    destination: str
    frequency_weekly: int
    fare_economy: float
    fare_business: float
    aircraft_type: str
    load_factor: float
    start_date: datetime

class AICompetitionManager:
    """Manages AI airline competition in the tycoon game"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ai_airlines = []
        self.ai_routes = []
        self.init_database()
        
    def init_database(self):
        """Initialize AI competition database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # AI Airlines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_airlines (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                iata_code TEXT UNIQUE,
                strategy TEXT,
                personality TEXT,
                cash_balance REAL,
                fleet_size INTEGER,
                hub_airport TEXT,
                market_share REAL,
                reputation REAL,
                preferred_aircraft TEXT, -- JSON array
                route_count INTEGER,
                monthly_revenue REAL,
                monthly_costs REAL,
                last_decision_date TEXT,
                created_date TEXT
            )
        """)
        
        # AI Routes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_routes (
                id TEXT PRIMARY KEY,
                airline_id TEXT,
                origin TEXT,
                destination TEXT,
                frequency_weekly INTEGER,
                fare_economy REAL,
                fare_business REAL,
                aircraft_type TEXT,
                load_factor REAL,
                start_date TEXT,
                FOREIGN KEY (airline_id) REFERENCES ai_airlines (id)
            )
        """)
        
        # Competition events table (for tracking AI decisions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competition_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                airline_id TEXT,
                event_type TEXT, -- 'route_start', 'route_stop', 'price_change', 'fleet_expansion'
                description TEXT,
                impact_score REAL,
                event_date TEXT,
                FOREIGN KEY (airline_id) REFERENCES ai_airlines (id)
            )
        """)
        
        conn.commit()
        conn.close()
        
    def initialize_ai_airlines(self, count: int = 8) -> List[AIAirline]:
        """Create initial AI airlines for the game"""
        
        # Realistic airline names and data
        airline_templates = [
            {"name": "GlobalWings Airways", "iata": "GW", "hub": "KJFK", "strategy": AIStrategy.PREMIUM},
            {"name": "SkyBridge International", "iata": "SB", "hub": "EGLL", "strategy": AIStrategy.BALANCED},
            {"name": "EconoFly", "iata": "EF", "hub": "KLAX", "strategy": AIStrategy.BUDGET},
            {"name": "Northern Express", "iata": "NE", "hub": "CYYZ", "strategy": AIStrategy.AGGRESSIVE},
            {"name": "Pacific Airlines", "iata": "PA", "hub": "KSFO", "strategy": AIStrategy.BALANCED},
            {"name": "Metro Connect", "iata": "MC", "hub": "KORD", "strategy": AIStrategy.BUDGET},
            {"name": "Continental Cross", "iata": "CC", "hub": "KATL", "strategy": AIStrategy.PREMIUM},
            {"name": "Rapid Air", "iata": "RA", "hub": "KLAS", "strategy": AIStrategy.AGGRESSIVE},
            {"name": "Heritage Airways", "iata": "HA", "hub": "KBOS", "strategy": AIStrategy.PREMIUM},
            {"name": "Freedom Express", "iata": "FE", "hub": "KMIA", "strategy": AIStrategy.BUDGET}
        ]
        
        aircraft_preferences = {
            AIStrategy.BUDGET: ["A320neo", "B737 MAX 8", "E175"],
            AIStrategy.BALANCED: ["A321neo", "B737 MAX 9", "A330-300"],
            AIStrategy.PREMIUM: ["A350-900", "B787-9", "A330-900"],
            AIStrategy.AGGRESSIVE: ["A320neo", "B737 MAX 8", "A321neo"]
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        ai_airlines = []
        
        for i in range(min(count, len(airline_templates))):
            template = airline_templates[i]
            
            # Random personality
            personality = random.choice(list(AIPersonality))
            
            # Starting finances based on strategy
            if template["strategy"] == AIStrategy.PREMIUM:
                cash_balance = random.uniform(150, 300)  # Premium airlines start with more cash
                fleet_size = random.randint(5, 12)
            elif template["strategy"] == AIStrategy.BUDGET:
                cash_balance = random.uniform(80, 150)   # Budget airlines start lean
                fleet_size = random.randint(3, 8)
            else:
                cash_balance = random.uniform(100, 200)  # Balanced/Aggressive middle ground
                fleet_size = random.randint(4, 10)
            
            airline = AIAirline(
                id=f"ai_{template['iata'].lower()}",
                name=template["name"],
                iata_code=template["iata"],
                strategy=template["strategy"],
                personality=personality,
                cash_balance=cash_balance,
                fleet_size=fleet_size,
                hub_airport=template["hub"],
                market_share=random.uniform(0.05, 0.15),
                reputation=random.uniform(0.6, 0.9),
                preferred_aircraft=aircraft_preferences[template["strategy"]],
                route_count=0,
                monthly_revenue=0.0,
                monthly_costs=0.0,
                last_decision_date=datetime.now()
            )
            
            ai_airlines.append(airline)
            
            # Insert into database
            cursor.execute("""
                INSERT OR REPLACE INTO ai_airlines 
                (id, name, iata_code, strategy, personality, cash_balance, fleet_size, 
                 hub_airport, market_share, reputation, preferred_aircraft, route_count,
                 monthly_revenue, monthly_costs, last_decision_date, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                airline.id, airline.name, airline.iata_code, airline.strategy.value,
                airline.personality.value, airline.cash_balance, airline.fleet_size,
                airline.hub_airport, airline.market_share, airline.reputation,
                json.dumps(airline.preferred_aircraft), airline.route_count,
                airline.monthly_revenue, airline.monthly_costs,
                airline.last_decision_date.isoformat(), datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        self.ai_airlines = ai_airlines
        return ai_airlines
    
    def simulate_ai_decisions(self) -> List[Dict]:
        """Simulate AI airline decision-making for the current time period"""
        decisions = []
        
        for airline in self.ai_airlines:
            # Each AI airline makes decisions based on their strategy and personality
            decision = self._make_ai_decision(airline)
            if decision:
                decisions.append(decision)
                self._execute_ai_decision(airline, decision)
        
        return decisions
    
    def _make_ai_decision(self, airline: AIAirline) -> Optional[Dict]:
        """Make a decision for a single AI airline"""
        
        # Decision frequency based on personality
        decision_chance = {
            AIPersonality.AGGRESSIVE: 0.8,
            AIPersonality.OPPORTUNISTIC: 0.6,
            AIPersonality.CAUTIOUS: 0.3,
            AIPersonality.SPECIALIST: 0.4
        }
        
        if random.random() > decision_chance[airline.personality]:
            return None
        
        # Possible decisions
        possible_decisions = []
        
        # Route expansion (if profitable and has cash)
        if airline.cash_balance > 50 and airline.fleet_size > airline.route_count:
            possible_decisions.append("expand_route")
        
        # Price adjustment (always possible)
        possible_decisions.append("adjust_pricing")
        
        # Fleet expansion (if very profitable)
        if airline.cash_balance > 150 and airline.monthly_revenue > airline.monthly_costs * 1.5:
            possible_decisions.append("expand_fleet")
        
        # Route abandonment (if losing money)
        if airline.monthly_revenue < airline.monthly_costs * 0.8 and airline.route_count > 1:
            possible_decisions.append("abandon_route")
        
        if not possible_decisions:
            return None
        
        decision_type = random.choice(possible_decisions)
        
        return {
            "airline_id": airline.id,
            "type": decision_type,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_ai_decision(self, airline: AIAirline, decision: Dict):
        """Execute an AI airline's decision"""
        decision_type = decision["type"]
        
        if decision_type == "expand_route":
            self._ai_expand_route(airline)
        elif decision_type == "adjust_pricing":
            self._ai_adjust_pricing(airline)
        elif decision_type == "expand_fleet":
            self._ai_expand_fleet(airline)
        elif decision_type == "abandon_route":
            self._ai_abandon_route(airline)
    
    def _ai_expand_route(self, airline: AIAirline):
        """AI airline starts a new route"""
        # Simple route selection - expand from hub to unserved destinations
        # In real implementation, this would check existing routes and competition
        
        destinations = ["KJFK", "KLAX", "KORD", "KATL", "KDEN", "KSFO", "KMIA", "KBOS"]
        available_destinations = [d for d in destinations if d != airline.hub_airport]
        
        if not available_destinations:
            return
        
        destination = random.choice(available_destinations)
        
        # Pricing based on strategy
        base_economy_fare = 250
        if airline.strategy == AIStrategy.BUDGET:
            fare_economy = base_economy_fare * random.uniform(0.7, 0.9)
        elif airline.strategy == AIStrategy.PREMIUM:
            fare_economy = base_economy_fare * random.uniform(1.2, 1.5)
        else:
            fare_economy = base_economy_fare * random.uniform(0.9, 1.2)
        
        # Create route
        route = AIRoute(
            id=f"{airline.id}_{airline.hub_airport}_{destination}",
            airline_id=airline.id,
            origin=airline.hub_airport,
            destination=destination,
            frequency_weekly=random.randint(3, 14),
            fare_economy=fare_economy,
            fare_business=fare_economy * 3.5,
            aircraft_type=random.choice(airline.preferred_aircraft),
            load_factor=random.uniform(0.65, 0.85),
            start_date=datetime.now()
        )
        
        # Save to database
        self._save_ai_route(route)
        airline.route_count += 1
        airline.cash_balance -= random.uniform(5, 15)  # Route startup costs
        
        # Log competition event
        self._log_competition_event(
            airline.id, 
            "route_start", 
            f"{airline.name} started route {airline.hub_airport}-{destination}",
            0.3
        )
    
    def _ai_adjust_pricing(self, airline: AIAirline):
        """AI airline adjusts pricing on existing routes"""
        # Simple price adjustment based on strategy
        adjustment_factor = 1.0
        
        if airline.strategy == AIStrategy.AGGRESSIVE:
            adjustment_factor = random.uniform(0.85, 0.95)  # Lower prices to compete
        elif airline.strategy == AIStrategy.PREMIUM:
            adjustment_factor = random.uniform(1.05, 1.15)  # Raise prices for premium
        elif airline.strategy == AIStrategy.BUDGET:
            adjustment_factor = random.uniform(0.80, 0.90)  # Always competitive pricing
        
        self._log_competition_event(
            airline.id,
            "price_change",
            f"{airline.name} adjusted pricing by {(adjustment_factor-1)*100:.1f}%",
            abs(adjustment_factor - 1) * 0.5
        )
    
    def _ai_expand_fleet(self, airline: AIAirline):
        """AI airline purchases new aircraft"""
        aircraft_cost = random.uniform(80, 150)  # Aircraft purchase cost
        if airline.cash_balance >= aircraft_cost:
            airline.fleet_size += 1
            airline.cash_balance -= aircraft_cost
            
            self._log_competition_event(
                airline.id,
                "fleet_expansion",
                f"{airline.name} purchased new aircraft",
                0.4
            )
    
    def _ai_abandon_route(self, airline: AIAirline):
        """AI airline stops operating a route"""
        if airline.route_count > 1:
            airline.route_count -= 1
            airline.cash_balance += random.uniform(2, 8)  # Some cost savings
            
            self._log_competition_event(
                airline.id,
                "route_stop",
                f"{airline.name} discontinued a route",
                0.2
            )
    
    def _save_ai_route(self, route: AIRoute):
        """Save AI route to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ai_routes
            (id, airline_id, origin, destination, frequency_weekly, fare_economy,
             fare_business, aircraft_type, load_factor, start_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            route.id, route.airline_id, route.origin, route.destination,
            route.frequency_weekly, route.fare_economy, route.fare_business,
            route.aircraft_type, route.load_factor, route.start_date.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _log_competition_event(self, airline_id: str, event_type: str, description: str, impact_score: float):
        """Log a competition event for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO competition_events
            (airline_id, event_type, description, impact_score, event_date)
            VALUES (?, ?, ?, ?, ?)
        """, (airline_id, event_type, description, impact_score, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_route_competition(self, origin: str, destination: str) -> Dict:
        """Get competition analysis for a specific route"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find AI airlines operating this route
        cursor.execute("""
            SELECT ai_airlines.name, ai_routes.frequency_weekly, ai_routes.fare_economy,
                   ai_airlines.strategy, ai_airlines.reputation
            FROM ai_routes
            JOIN ai_airlines ON ai_routes.airline_id = ai_airlines.id
            WHERE (ai_routes.origin = ? AND ai_routes.destination = ?)
               OR (ai_routes.origin = ? AND ai_routes.destination = ?)
        """, (origin, destination, destination, origin))
        
        competitors = cursor.fetchall()
        conn.close()
        
        if not competitors:
            return {"competition_level": 0, "competitors": [], "avg_fare": 0}
        
        total_frequency = sum(comp[1] for comp in competitors)
        avg_fare = sum(comp[2] for comp in competitors) / len(competitors)
        
        return {
            "competition_level": min(10, len(competitors) * 2 + total_frequency // 10),
            "competitors": [{"name": comp[0], "strategy": comp[3], "reputation": comp[4]} for comp in competitors],
            "avg_fare": avg_fare,
            "total_weekly_frequency": total_frequency
        }
    
    def get_market_share_impact(self, player_revenue: float) -> float:
        """Calculate how player performance affects AI airline market share"""
        total_ai_revenue = sum(airline.monthly_revenue for airline in self.ai_airlines)
        total_market = player_revenue + total_ai_revenue
        
        if total_market == 0:
            return 0.0
        
        player_market_share = player_revenue / total_market
        
        # If player is doing well, AI airlines feel pressure
        if player_market_share > 0.3:
            return -0.05  # AI airlines become more aggressive
        elif player_market_share < 0.1:
            return 0.02   # AI airlines become complacent
        
        return 0.0

# Example usage and testing
if __name__ == "__main__":
    # Initialize AI competition system
    ai_manager = AICompetitionManager("airline_game.db")
    
    # Create AI airlines
    airlines = ai_manager.initialize_ai_airlines(5)
    
    print("=== AI Airlines Initialized ===")
    for airline in airlines:
        print(f"{airline.name} ({airline.iata_code})")
        print(f"  Strategy: {airline.strategy.value}")
        print(f"  Personality: {airline.personality.value}")
        print(f"  Hub: {airline.hub_airport}")
        print(f"  Cash: ${airline.cash_balance:.1f}M")
        print(f"  Fleet: {airline.fleet_size} aircraft")
        print()
    
    # Simulate some decisions
    print("=== Simulating AI Decisions ===")
    for _ in range(3):
        decisions = ai_manager.simulate_ai_decisions()
        for decision in decisions:
            print(f"AI Decision: {decision}")
    
    # Check route competition
    competition = ai_manager.get_route_competition("KJFK", "KLAX")
    print(f"\nRoute Competition (JFK-LAX): {competition}")