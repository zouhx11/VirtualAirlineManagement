# modules/market_competition.py

import sqlite3
import json
import random
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import uuid

from modules.route_management import RouteEconomics, RouteData
from modules.aircraft_marketplace import AircraftMarketplace

class CompetitorType(Enum):
    LEGACY_CARRIER = "legacy_carrier"
    LOW_COST_CARRIER = "low_cost_carrier"
    REGIONAL_CARRIER = "regional_carrier"
    CARGO_CARRIER = "cargo_carrier"
    LUXURY_CARRIER = "luxury_carrier"

class AllianceType(Enum):
    STAR_ALLIANCE = "star_alliance"
    ONEWORLD = "oneworld"
    SKYTEAM = "skyteam"
    INDEPENDENT = "independent"

class CompetitiveStrategy(Enum):
    AGGRESSIVE_PRICING = "aggressive_pricing"
    PREMIUM_SERVICE = "premium_service"
    ROUTE_EXPANSION = "route_expansion"
    EFFICIENCY_FOCUS = "efficiency_focus"
    MARKET_DEFENSE = "market_defense"

@dataclass
class CompetitorAirline:
    """AI-controlled competitor airline"""
    id: str
    name: str
    icao_code: str
    iata_code: str
    competitor_type: CompetitorType
    alliance: AllianceType
    hub_airports: List[str]  # Primary hub airports
    focus_regions: List[str]  # Geographic focus areas
    
    # Financial data
    cash_reserves: float  # Million USD
    market_cap: float  # Million USD
    debt_ratio: float  # 0-1 scale
    
    # Operational data
    fleet_size: int
    route_count: int
    annual_passengers: int  # Millions
    load_factor: float  # Average load factor
    
    # Strategy and behavior
    strategy: CompetitiveStrategy
    aggressiveness: float  # 0-1 scale
    risk_tolerance: float  # 0-1 scale
    expansion_rate: float  # Routes added per month
    
    # Market position
    market_share: Dict[str, float]  # Route ID -> market share
    reputation_score: float  # 0-100 scale
    on_time_performance: float  # 0-1 scale
    
    # Alliance data
    alliance_benefits: List[str]
    codeshare_partners: List[str]
    
    created_date: datetime
    last_strategy_change: datetime

@dataclass
class RouteCompetition:
    """Competition data for a specific route"""
    route_id: str
    competitors: List[str]  # Competitor airline IDs
    market_shares: Dict[str, float]  # Airline ID -> market share
    pricing_data: Dict[str, Dict[str, float]]  # Airline ID -> {economy_fare, business_fare}
    frequency_data: Dict[str, int]  # Airline ID -> weekly frequency
    service_quality: Dict[str, float]  # Airline ID -> service rating (0-100)
    
    # Market dynamics
    total_weekly_capacity: int
    total_weekly_demand: int
    market_saturation: float  # 0-1 scale
    price_sensitivity: float  # How much demand responds to price changes
    
    # Competition metrics
    herfindahl_index: float  # Market concentration (0-10000)
    price_war_active: bool
    dominant_carrier: Optional[str]  # Airline ID with >50% market share
    
    last_updated: datetime

@dataclass
class Alliance:
    """Airline alliance for cooperation"""
    id: str
    name: str
    alliance_type: AllianceType
    member_airlines: List[str]  # Airline IDs
    
    # Benefits
    route_sharing_enabled: bool
    frequent_flyer_reciprocity: bool
    lounge_access_sharing: bool
    coordinated_schedules: bool
    
    # Performance
    combined_market_share: Dict[str, float]  # Route ID -> combined share
    revenue_sharing_percentage: float  # 0-1 scale
    
    founded_date: datetime

class MarketCompetition:
    """Market competition simulation engine"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.route_economics = RouteEconomics(db_path)
        self.aircraft_marketplace = AircraftMarketplace(db_path)
        self.init_database()
        self.load_competitor_templates()
        
    def init_database(self):
        """Initialize market competition database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Competitor airlines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_airlines (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                icao_code TEXT NOT NULL,
                iata_code TEXT NOT NULL,
                competitor_type TEXT NOT NULL,
                alliance TEXT NOT NULL,
                hub_airports TEXT NOT NULL,
                focus_regions TEXT NOT NULL,
                cash_reserves REAL NOT NULL,
                market_cap REAL NOT NULL,
                debt_ratio REAL NOT NULL,
                fleet_size INTEGER NOT NULL,
                route_count INTEGER NOT NULL,
                annual_passengers INTEGER NOT NULL,
                load_factor REAL NOT NULL,
                strategy TEXT NOT NULL,
                aggressiveness REAL NOT NULL,
                risk_tolerance REAL NOT NULL,
                expansion_rate REAL NOT NULL,
                market_share TEXT NOT NULL,
                reputation_score REAL NOT NULL,
                on_time_performance REAL NOT NULL,
                alliance_benefits TEXT NOT NULL,
                codeshare_partners TEXT NOT NULL,
                created_date TEXT NOT NULL,
                last_strategy_change TEXT NOT NULL
            )
        ''')
        
        # Route competition table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_competition (
                route_id TEXT PRIMARY KEY,
                competitors TEXT NOT NULL,
                market_shares TEXT NOT NULL,
                pricing_data TEXT NOT NULL,
                frequency_data TEXT NOT NULL,
                service_quality TEXT NOT NULL,
                total_weekly_capacity INTEGER NOT NULL,
                total_weekly_demand INTEGER NOT NULL,
                market_saturation REAL NOT NULL,
                price_sensitivity REAL NOT NULL,
                herfindahl_index REAL NOT NULL,
                price_war_active INTEGER NOT NULL,
                dominant_carrier TEXT,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (route_id) REFERENCES routes (id)
            )
        ''')
        
        # Alliances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliances (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                alliance_type TEXT NOT NULL,
                member_airlines TEXT NOT NULL,
                route_sharing_enabled INTEGER NOT NULL,
                frequent_flyer_reciprocity INTEGER NOT NULL,
                lounge_access_sharing INTEGER NOT NULL,
                coordinated_schedules INTEGER NOT NULL,
                combined_market_share TEXT NOT NULL,
                revenue_sharing_percentage REAL NOT NULL,
                founded_date TEXT NOT NULL
            )
        ''')
        
        # Competitive events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitive_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                airline_id TEXT,
                route_id TEXT,
                description TEXT NOT NULL,
                impact_score REAL NOT NULL,
                event_date TEXT NOT NULL,
                event_data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_competitor_templates(self):
        """Load realistic competitor airline templates"""
        self.competitor_templates = [
            {
                "name": "SkyWings International", "icao": "SKW", "iata": "SW",
                "type": CompetitorType.LEGACY_CARRIER, "alliance": AllianceType.STAR_ALLIANCE,
                "hubs": ["KJFK", "KLAX"], "regions": ["North America", "Europe"],
                "market_cap": 12000, "fleet_size": 285, "reputation": 82
            },
            {
                "name": "Pacific Express", "icao": "PEX", "iata": "PX", 
                "type": CompetitorType.LOW_COST_CARRIER, "alliance": AllianceType.INDEPENDENT,
                "hubs": ["KLAS", "KPHX"], "regions": ["North America", "Central America"],
                "market_cap": 4500, "fleet_size": 156, "reputation": 73
            },
            {
                "name": "Northern Regional", "icao": "NRG", "iata": "NR",
                "type": CompetitorType.REGIONAL_CARRIER, "alliance": AllianceType.INDEPENDENT,
                "hubs": ["KORD", "KDEN"], "regions": ["North America"],
                "market_cap": 1800, "fleet_size": 89, "reputation": 78
            },
            {
                "name": "Global Premium Airways", "icao": "GPA", "iata": "GP",
                "type": CompetitorType.LUXURY_CARRIER, "alliance": AllianceType.ONEWORLD,
                "hubs": ["EGLL", "LFPG"], "regions": ["Europe", "Asia", "North America"],
                "market_cap": 18500, "fleet_size": 198, "reputation": 91
            },
            {
                "name": "Transcontinental Cargo", "icao": "TCC", "iata": "TC",
                "type": CompetitorType.CARGO_CARRIER, "alliance": AllianceType.INDEPENDENT,
                "hubs": ["KMEM", "KCVG"], "regions": ["Global"],
                "market_cap": 8200, "fleet_size": 124, "reputation": 85
            },
            {
                "name": "European Connect", "icao": "EUC", "iata": "EU",
                "type": CompetitorType.LEGACY_CARRIER, "alliance": AllianceType.SKYTEAM,
                "hubs": ["EDDF", "EHAM"], "regions": ["Europe", "Africa"],
                "market_cap": 9800, "fleet_size": 167, "reputation": 84
            },
            {
                "name": "Asian Star Airlines", "icao": "ASA", "iata": "AS",
                "type": CompetitorType.LEGACY_CARRIER, "alliance": AllianceType.STAR_ALLIANCE,
                "hubs": ["RJTT", "WSSS"], "regions": ["Asia", "Australia"],
                "market_cap": 15200, "fleet_size": 234, "reputation": 88
            },
            {
                "name": "Budget Wings", "icao": "BWG", "iata": "BW",
                "type": CompetitorType.LOW_COST_CARRIER, "alliance": AllianceType.INDEPENDENT,
                "hubs": ["KBOS", "KMCO"], "regions": ["North America"],
                "market_cap": 3200, "fleet_size": 98, "reputation": 69
            }
        ]
    
    def generate_competitor_airlines(self, count: int = 8) -> List[CompetitorAirline]:
        """Generate AI competitor airlines"""
        competitors = []
        
        for i, template in enumerate(self.competitor_templates[:count]):
            competitor_id = f"COMP_{template['icao']}_{random.randint(1000, 9999)}"
            
            # Generate strategy based on carrier type
            strategy = self._determine_strategy(template['type'])
            
            # Generate financial metrics
            cash_reserves = template['market_cap'] * random.uniform(0.15, 0.35)
            debt_ratio = random.uniform(0.2, 0.6)
            
            # Generate operational metrics  
            annual_passengers = template['fleet_size'] * random.uniform(0.8, 1.2) * 100  # Rough estimate
            load_factor = random.uniform(0.75, 0.88)
            
            # Generate behavior characteristics
            aggressiveness = self._get_aggressiveness_by_type(template['type'])
            risk_tolerance = random.uniform(0.3, 0.8)
            expansion_rate = random.uniform(1, 5)  # Routes per month
            
            competitor = CompetitorAirline(
                id=competitor_id,
                name=template['name'],
                icao_code=template['icao'],
                iata_code=template['iata'],
                competitor_type=template['type'],
                alliance=template['alliance'],
                hub_airports=template['hubs'],
                focus_regions=template['regions'],
                cash_reserves=cash_reserves,
                market_cap=template['market_cap'],
                debt_ratio=debt_ratio,
                fleet_size=template['fleet_size'],
                route_count=random.randint(50, 200),
                annual_passengers=int(annual_passengers),
                load_factor=load_factor,
                strategy=strategy,
                aggressiveness=aggressiveness,
                risk_tolerance=risk_tolerance,
                expansion_rate=expansion_rate,
                market_share={},
                reputation_score=template['reputation'],
                on_time_performance=random.uniform(0.78, 0.92),
                alliance_benefits=self._get_alliance_benefits(template['alliance']),
                codeshare_partners=[],
                created_date=datetime.now(),
                last_strategy_change=datetime.now() - timedelta(days=random.randint(30, 180))
            )
            
            competitors.append(competitor)
        
        return competitors
    
    def _determine_strategy(self, carrier_type: CompetitorType) -> CompetitiveStrategy:
        """Determine competitive strategy based on carrier type"""
        strategy_weights = {
            CompetitorType.LEGACY_CARRIER: {
                CompetitiveStrategy.PREMIUM_SERVICE: 0.4,
                CompetitiveStrategy.MARKET_DEFENSE: 0.3,
                CompetitiveStrategy.ROUTE_EXPANSION: 0.2,
                CompetitiveStrategy.EFFICIENCY_FOCUS: 0.1
            },
            CompetitorType.LOW_COST_CARRIER: {
                CompetitiveStrategy.AGGRESSIVE_PRICING: 0.6,
                CompetitiveStrategy.EFFICIENCY_FOCUS: 0.25,
                CompetitiveStrategy.ROUTE_EXPANSION: 0.15
            },
            CompetitorType.REGIONAL_CARRIER: {
                CompetitiveStrategy.MARKET_DEFENSE: 0.4,
                CompetitiveStrategy.EFFICIENCY_FOCUS: 0.3,
                CompetitiveStrategy.ROUTE_EXPANSION: 0.3
            },
            CompetitorType.LUXURY_CARRIER: {
                CompetitiveStrategy.PREMIUM_SERVICE: 0.7,
                CompetitiveStrategy.MARKET_DEFENSE: 0.3
            },
            CompetitorType.CARGO_CARRIER: {
                CompetitiveStrategy.EFFICIENCY_FOCUS: 0.5,
                CompetitiveStrategy.ROUTE_EXPANSION: 0.3,
                CompetitiveStrategy.MARKET_DEFENSE: 0.2
            }
        }
        
        weights = strategy_weights[carrier_type]
        strategies = list(weights.keys())
        probabilities = list(weights.values())
        
        return random.choices(strategies, weights=probabilities)[0]
    
    def _get_aggressiveness_by_type(self, carrier_type: CompetitorType) -> float:
        """Get aggressiveness level based on carrier type"""
        aggressiveness_ranges = {
            CompetitorType.LEGACY_CARRIER: (0.3, 0.6),
            CompetitorType.LOW_COST_CARRIER: (0.6, 0.9),
            CompetitorType.REGIONAL_CARRIER: (0.2, 0.5),
            CompetitorType.LUXURY_CARRIER: (0.1, 0.4),
            CompetitorType.CARGO_CARRIER: (0.3, 0.7)
        }
        
        min_agg, max_agg = aggressiveness_ranges[carrier_type]
        return random.uniform(min_agg, max_agg)
    
    def _get_alliance_benefits(self, alliance: AllianceType) -> List[str]:
        """Get benefits based on alliance membership"""
        if alliance == AllianceType.INDEPENDENT:
            return ["flexibility", "independent_pricing"]
        
        return [
            "route_sharing",
            "frequent_flyer_reciprocity", 
            "lounge_access",
            "coordinated_schedules",
            "bulk_purchasing",
            "maintenance_sharing"
        ]
    
    def save_competitors(self, competitors: List[CompetitorAirline]):
        """Save competitor airlines to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing competitors
        cursor.execute("DELETE FROM competitor_airlines")
        
        for competitor in competitors:
            cursor.execute('''
                INSERT INTO competitor_airlines VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                competitor.id,
                competitor.name,
                competitor.icao_code,
                competitor.iata_code,
                competitor.competitor_type.value,
                competitor.alliance.value,
                json.dumps(competitor.hub_airports),
                json.dumps(competitor.focus_regions),
                competitor.cash_reserves,
                competitor.market_cap,
                competitor.debt_ratio,
                competitor.fleet_size,
                competitor.route_count,
                competitor.annual_passengers,
                competitor.load_factor,
                competitor.strategy.value,
                competitor.aggressiveness,
                competitor.risk_tolerance,
                competitor.expansion_rate,
                json.dumps(competitor.market_share),
                competitor.reputation_score,
                competitor.on_time_performance,
                json.dumps(competitor.alliance_benefits),
                json.dumps(competitor.codeshare_partners),
                competitor.created_date.isoformat(),
                competitor.last_strategy_change.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_competitors(self) -> List[CompetitorAirline]:
        """Get all competitor airlines from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM competitor_airlines")
        rows = cursor.fetchall()
        conn.close()
        
        competitors = []
        for row in rows:
            competitor = CompetitorAirline(
                id=row[0],
                name=row[1],
                icao_code=row[2],
                iata_code=row[3],
                competitor_type=CompetitorType(row[4]),
                alliance=AllianceType(row[5]),
                hub_airports=json.loads(row[6]),
                focus_regions=json.loads(row[7]),
                cash_reserves=row[8],
                market_cap=row[9],
                debt_ratio=row[10],
                fleet_size=row[11],
                route_count=row[12],
                annual_passengers=row[13],
                load_factor=row[14],
                strategy=CompetitiveStrategy(row[15]),
                aggressiveness=row[16],
                risk_tolerance=row[17],
                expansion_rate=row[18],
                market_share=json.loads(row[19]),
                reputation_score=row[20],
                on_time_performance=row[21],
                alliance_benefits=json.loads(row[22]),
                codeshare_partners=json.loads(row[23]),
                created_date=datetime.fromisoformat(row[24]),
                last_strategy_change=datetime.fromisoformat(row[25])
            )
            competitors.append(competitor)
        
        return competitors
    
    def simulate_route_competition(self, route_id: str, player_entry: bool = False) -> RouteCompetition:
        """Simulate competition on a specific route"""
        competitors = self.get_competitors()
        route_competitors = []
        
        # Determine which competitors operate this route
        routes = self.route_economics.get_routes()
        route = next((r for r in routes if r.id == route_id), None)
        
        if not route:
            raise ValueError(f"Route {route_id} not found")
        
        # Select competitors based on their strategy and hub proximity
        for competitor in competitors:
            operates_route = self._competitor_operates_route(competitor, route)
            if operates_route:
                route_competitors.append(competitor.id)
        
        # Ensure minimum competition
        if len(route_competitors) < 2:
            additional_competitors = random.sample(
                [c.id for c in competitors if c.id not in route_competitors],
                min(2 - len(route_competitors), len(competitors) - len(route_competitors))
            )
            route_competitors.extend(additional_competitors)
        
        # Calculate market shares
        market_shares = self._calculate_market_shares(route_competitors, competitors, route)
        
        # Generate pricing data
        pricing_data = self._generate_competitive_pricing(route_competitors, competitors, route)
        
        # Generate frequency data
        frequency_data = self._generate_frequency_data(route_competitors, competitors)
        
        # Calculate service quality
        service_quality = {comp_id: next(c.reputation_score for c in competitors if c.id == comp_id) 
                          for comp_id in route_competitors}
        
        # Calculate market metrics
        total_capacity = sum(frequency_data.values()) * 180  # Assume average 180 seats
        base_demand = self._estimate_route_demand(route)
        total_demand = int(base_demand * len(route_competitors) * 0.8)  # Competition increases demand
        
        market_saturation = total_capacity / total_demand if total_demand > 0 else 1.0
        price_sensitivity = 0.8 - (route.distance_nm / 10000)  # Longer routes less price sensitive
        
        # Calculate Herfindahl Index (market concentration)
        herfindahl_index = sum(share ** 2 for share in market_shares.values()) * 10000
        
        # Determine if price war is active
        price_war_active = herfindahl_index < 2500 and market_saturation > 0.9
        
        # Find dominant carrier
        dominant_carrier = None
        for airline_id, share in market_shares.items():
            if share > 0.5:
                dominant_carrier = airline_id
                break
        
        competition = RouteCompetition(
            route_id=route_id,
            competitors=route_competitors,
            market_shares=market_shares,
            pricing_data=pricing_data,
            frequency_data=frequency_data,
            service_quality=service_quality,
            total_weekly_capacity=total_capacity,
            total_weekly_demand=total_demand,
            market_saturation=market_saturation,
            price_sensitivity=price_sensitivity,
            herfindahl_index=herfindahl_index,
            price_war_active=price_war_active,
            dominant_carrier=dominant_carrier,
            last_updated=datetime.now()
        )
        
        return competition
    
    def _competitor_operates_route(self, competitor: CompetitorAirline, route: RouteData) -> bool:
        """Determine if a competitor operates on a given route"""
        # Check if route connects to competitor's hubs
        hub_connection = (route.origin_icao in competitor.hub_airports or 
                         route.destination_icao in competitor.hub_airports)
        
        if hub_connection:
            return True
        
        # Check if route is in competitor's focus regions (simplified)
        # For now, assume geographic probability based on carrier type
        if competitor.competitor_type == CompetitorType.REGIONAL_CARRIER:
            return route.distance_nm < 1500 and random.random() < 0.6
        elif competitor.competitor_type == CompetitorType.LOW_COST_CARRIER:
            return route.distance_nm < 2500 and random.random() < 0.4
        else:
            return random.random() < 0.3  # General probability
    
    def _calculate_market_shares(self, route_competitors: List[str], 
                                competitors: List[CompetitorAirline], 
                                route: RouteData) -> Dict[str, float]:
        """Calculate market shares for competitors on a route"""
        shares = {}
        total_strength = 0
        
        # Calculate competitive strength for each airline
        strengths = {}
        for comp_id in route_competitors:
            competitor = next(c for c in competitors if c.id == comp_id)
            
            # Base strength factors
            fleet_strength = min(competitor.fleet_size / 100, 2.0)
            reputation_strength = competitor.reputation_score / 100
            financial_strength = min(competitor.market_cap / 10000, 2.0)
            
            # Strategy modifiers
            strategy_modifier = self._get_strategy_strength(competitor.strategy, route)
            
            # Alliance benefits
            alliance_modifier = 1.2 if competitor.alliance != AllianceType.INDEPENDENT else 1.0
            
            strength = (fleet_strength + reputation_strength + financial_strength) * strategy_modifier * alliance_modifier
            strengths[comp_id] = strength
            total_strength += strength
        
        # Convert strengths to market shares
        for comp_id, strength in strengths.items():
            shares[comp_id] = strength / total_strength if total_strength > 0 else 1.0 / len(route_competitors)
        
        return shares
    
    def _get_strategy_strength(self, strategy: CompetitiveStrategy, route: RouteData) -> float:
        """Get strategy strength modifier based on route characteristics"""
        base_modifier = 1.0
        
        if strategy == CompetitiveStrategy.AGGRESSIVE_PRICING:
            return base_modifier + 0.3  # Always helps with market share
        elif strategy == CompetitiveStrategy.PREMIUM_SERVICE:
            return base_modifier + (0.4 if route.distance_nm > 2000 else 0.1)  # Better on long routes
        elif strategy == CompetitiveStrategy.ROUTE_EXPANSION:
            return base_modifier + 0.2
        elif strategy == CompetitiveStrategy.EFFICIENCY_FOCUS:
            return base_modifier + 0.15
        else:  # MARKET_DEFENSE
            return base_modifier + 0.1
    
    def _generate_competitive_pricing(self, route_competitors: List[str], 
                                    competitors: List[CompetitorAirline], 
                                    route: RouteData) -> Dict[str, Dict[str, float]]:
        """Generate competitive pricing for each airline"""
        pricing_data = {}
        market_fare = route.market_fare_economy
        
        for comp_id in route_competitors:
            competitor = next(c for c in competitors if c.id == comp_id)
            
            # Base pricing strategy
            if competitor.strategy == CompetitiveStrategy.AGGRESSIVE_PRICING:
                price_modifier = random.uniform(0.7, 0.9)
            elif competitor.strategy == CompetitiveStrategy.PREMIUM_SERVICE:
                price_modifier = random.uniform(1.1, 1.4)
            elif competitor.competitor_type == CompetitorType.LOW_COST_CARRIER:
                price_modifier = random.uniform(0.6, 0.8)
            elif competitor.competitor_type == CompetitorType.LUXURY_CARRIER:
                price_modifier = random.uniform(1.3, 1.8)
            else:
                price_modifier = random.uniform(0.9, 1.1)
            
            economy_fare = market_fare * price_modifier
            business_fare = economy_fare * random.uniform(3.0, 4.5)
            
            pricing_data[comp_id] = {
                "economy_fare": economy_fare,
                "business_fare": business_fare
            }
        
        return pricing_data
    
    def _generate_frequency_data(self, route_competitors: List[str], 
                               competitors: List[CompetitorAirline]) -> Dict[str, int]:
        """Generate flight frequency for each competitor"""
        frequency_data = {}
        
        for comp_id in route_competitors:
            competitor = next(c for c in competitors if c.id == comp_id)
            
            # Base frequency based on carrier type
            if competitor.competitor_type == CompetitorType.REGIONAL_CARRIER:
                base_frequency = random.randint(7, 14)  # 1-2 times daily
            elif competitor.competitor_type == CompetitorType.LOW_COST_CARRIER:
                base_frequency = random.randint(7, 21)  # 1-3 times daily
            else:
                base_frequency = random.randint(14, 28)  # 2-4 times daily
            
            # Strategy modifier
            if competitor.strategy == CompetitiveStrategy.ROUTE_EXPANSION:
                base_frequency = int(base_frequency * 1.3)
            elif competitor.strategy == CompetitiveStrategy.MARKET_DEFENSE:
                base_frequency = int(base_frequency * 1.2)
            
            frequency_data[comp_id] = base_frequency
        
        return frequency_data
    
    def _estimate_route_demand(self, route: RouteData) -> int:
        """Estimate weekly passenger demand for a route"""
        # Base demand calculation (simplified)
        base_demand = 2000  # Base weekly passengers
        
        # Distance modifier
        if route.distance_nm < 500:
            distance_modifier = 1.5  # High demand for short routes
        elif route.distance_nm < 1500:
            distance_modifier = 1.2
        elif route.distance_nm < 3000:
            distance_modifier = 1.0
        else:
            distance_modifier = 0.8  # Lower demand for very long routes
        
        # Demand level modifier
        demand_modifiers = {
            "very_low": 0.3,
            "low": 0.5,
            "medium": 0.7,
            "high": 1.0,
            "very_high": 1.4
        }
        
        demand_modifier = demand_modifiers.get(route.base_demand.value, 0.7)
        
        total_demand = int(base_demand * distance_modifier * demand_modifier)
        return total_demand
    
    def save_route_competition(self, competition: RouteCompetition):
        """Save route competition data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO route_competition VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            competition.route_id,
            json.dumps(competition.competitors),
            json.dumps(competition.market_shares),
            json.dumps(competition.pricing_data),
            json.dumps(competition.frequency_data),
            json.dumps(competition.service_quality),
            competition.total_weekly_capacity,
            competition.total_weekly_demand,
            competition.market_saturation,
            competition.price_sensitivity,
            competition.herfindahl_index,
            1 if competition.price_war_active else 0,
            competition.dominant_carrier,
            competition.last_updated.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_route_competition(self, route_id: str) -> Optional[RouteCompetition]:
        """Get route competition data from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM route_competition WHERE route_id = ?", (route_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        competition = RouteCompetition(
            route_id=row[0],
            competitors=json.loads(row[1]),
            market_shares=json.loads(row[2]),
            pricing_data=json.loads(row[3]),
            frequency_data=json.loads(row[4]),
            service_quality=json.loads(row[5]),
            total_weekly_capacity=row[6],
            total_weekly_demand=row[7],
            market_saturation=row[8],
            price_sensitivity=row[9],
            herfindahl_index=row[10],
            price_war_active=bool(row[11]),
            dominant_carrier=row[12],
            last_updated=datetime.fromisoformat(row[13])
        )
        
        return competition
    
    def calculate_competitive_impact(self, route_id: str, player_pricing: Dict[str, float], 
                                   player_frequency: int) -> Dict[str, float]:
        """Calculate impact of player entry/changes on route competition"""
        competition = self.get_route_competition(route_id)
        if not competition:
            # Generate competition if it doesn't exist
            competition = self.simulate_route_competition(route_id, player_entry=True)
            self.save_route_competition(competition)
        
        # Calculate player's competitive strength
        player_economy_fare = player_pricing.get("economy_fare", 0)
        player_business_fare = player_pricing.get("business_fare", 0)
        
        # Price competitiveness (lower is better for market share)
        avg_competitor_economy = sum(data["economy_fare"] for data in competition.pricing_data.values()) / len(competition.pricing_data)
        price_advantage = (avg_competitor_economy - player_economy_fare) / avg_competitor_economy
        
        # Frequency competitiveness
        avg_competitor_frequency = sum(competition.frequency_data.values()) / len(competition.frequency_data)
        frequency_advantage = (player_frequency - avg_competitor_frequency) / avg_competitor_frequency
        
        # Calculate market share impact
        base_share = 1.0 / (len(competition.competitors) + 1)  # Equal share baseline
        
        price_impact = price_advantage * competition.price_sensitivity * 0.3
        frequency_impact = frequency_advantage * 0.2
        
        estimated_share = base_share + price_impact + frequency_impact
        estimated_share = max(0.05, min(0.6, estimated_share))  # Cap between 5% and 60%
        
        # Calculate revenue impact
        total_weekly_passengers = competition.total_weekly_demand * estimated_share
        weekly_revenue = total_weekly_passengers * (player_economy_fare * 0.85 + player_business_fare * 0.15)
        monthly_revenue = weekly_revenue * 4.33
        
        return {
            "estimated_market_share": estimated_share,
            "price_advantage": price_advantage,
            "frequency_advantage": frequency_advantage,
            "weekly_passengers": total_weekly_passengers,
            "monthly_revenue": monthly_revenue,
            "competition_intensity": competition.herfindahl_index / 10000,
            "price_war_risk": competition.price_war_active
        }

# Example usage
if __name__ == "__main__":
    # Initialize market competition system
    market = MarketCompetition("userdata.db")
    
    # Generate competitor airlines
    competitors = market.generate_competitor_airlines(8)
    market.save_competitors(competitors)
    
    print("=== Market Competition System ===")
    print(f"Generated {len(competitors)} competitor airlines:")
    
    for competitor in competitors:
        print(f"\n{competitor.name} ({competitor.icao_code})")
        print(f"  Type: {competitor.competitor_type.value.replace('_', ' ').title()}")
        print(f"  Strategy: {competitor.strategy.value.replace('_', ' ').title()}")
        print(f"  Alliance: {competitor.alliance.value.replace('_', ' ').title()}")
        print(f"  Fleet Size: {competitor.fleet_size} aircraft")
        print(f"  Market Cap: ${competitor.market_cap:,.0f}M")
        print(f"  Reputation: {competitor.reputation_score:.0f}/100")
    
    # Simulate competition on a sample route
    routes = market.route_economics.get_routes()
    if routes:
        sample_route = routes[0]
        competition = market.simulate_route_competition(sample_route.id)
        market.save_route_competition(competition)
        
        print(f"\n=== Competition Analysis: {sample_route.origin_icao} → {sample_route.destination_icao} ===")
        print(f"Competitors: {len(competition.competitors)}")
        print(f"Market Concentration (HHI): {competition.herfindahl_index:.0f}")
        print(f"Price War Active: {competition.price_war_active}")
        print(f"Market Saturation: {competition.market_saturation:.1%}")
        
        print("\nMarket Shares:")
        for airline_id, share in competition.market_shares.items():
            competitor_name = next(c.name for c in competitors if c.id == airline_id)
            print(f"  {competitor_name}: {share:.1%}")