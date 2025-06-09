# modules/aircraft_marketplace.py

import sqlite3
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import random
import math

class AircraftCondition(Enum):
    NEW = "new"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class AircraftCategory(Enum):
    REGIONAL = "regional"
    NARROW_BODY = "narrow_body"
    WIDE_BODY = "wide_body"
    CARGO = "cargo"
    BUSINESS_JET = "business_jet"

class FinancingType(Enum):
    CASH = "cash"
    LEASE = "lease"
    LOAN = "loan"

@dataclass
class AircraftSpec:
    """Comprehensive aircraft specifications"""
    model: str
    manufacturer: str
    category: AircraftCategory
    passenger_capacity: int
    cargo_capacity: float  # tons
    max_range: int  # nautical miles
    cruise_speed: int  # knots
    fuel_capacity: float  # gallons
    fuel_burn_per_hour: float  # gallons per hour
    mtow: float  # maximum takeoff weight in tons
    runway_length_required: int  # feet
    base_price: float  # new aircraft price in millions USD
    annual_maintenance_cost: float  # percentage of aircraft value
    crew_required: int
    introduction_year: int

@dataclass
class MarketAircraft:
    """Aircraft available for purchase/lease in the marketplace"""
    id: str
    spec: AircraftSpec
    condition: AircraftCondition
    age_years: float
    total_flight_hours: int
    cycles: int  # takeoff/landing cycles
    asking_price: float  # millions USD
    lease_rate_monthly: float  # thousands USD per month
    seller_type: str  # "manufacturer", "airline", "leasing_company"
    location: str  # airport code where aircraft is located
    available_until: datetime
    maintenance_due_hours: int  # hours until next major maintenance
    financing_available: List[FinancingType]

@dataclass
class OwnedAircraft:
    """Aircraft owned by the player's airline"""
    id: str
    spec: AircraftSpec
    condition: AircraftCondition
    age_years: float
    total_flight_hours: int
    cycles: int
    purchase_price: float
    current_value: float
    financing_type: FinancingType
    monthly_payment: float
    remaining_payments: int
    location: str  # current airport
    maintenance_due_hours: int
    last_maintenance: datetime
    utilization_hours_month: float
    route_assignments: List[str]  # route IDs assigned to this aircraft

class AircraftDatabase:
    """Manages aircraft specifications and market data"""
    
    def __init__(self):
        # Real-world aircraft specifications
        self.aircraft_specs = {
            # Regional Aircraft
            "ATR 72-600": AircraftSpec(
                "ATR 72-600", "ATR", AircraftCategory.REGIONAL, 78, 7.5, 825, 276,
                1273, 210, 23, 4265, 23.0, 2.5, 2, 2010
            ),
            "Embraer E175": AircraftSpec(
                "Embraer E175", "Embraer", AircraftCategory.REGIONAL, 88, 10.2, 2200, 460,
                2590, 320, 38.7, 6200, 53.0, 2.8, 2, 2004
            ),
            "CRJ-900": AircraftSpec(
                "CRJ-900", "Bombardier", AircraftCategory.REGIONAL, 90, 11.3, 1553, 470,
                2070, 340, 38.3, 5500, 47.0, 3.0, 2, 2003
            ),
            
            # Narrow Body
            "A320neo": AircraftSpec(
                "A320neo", "Airbus", AircraftCategory.NARROW_BODY, 180, 24.4, 3500, 454,
                6400, 650, 79, 7400, 110.0, 2.2, 2, 2016
            ),
            "A321XLR": AircraftSpec(
                "A321XLR", "Airbus", AircraftCategory.NARROW_BODY, 220, 32.9, 4700, 454,
                8700, 750, 97, 8200, 142.0, 2.3, 2, 2023
            ),
            "B737 MAX 8": AircraftSpec(
                "B737 MAX 8", "Boeing", AircraftCategory.NARROW_BODY, 178, 23.7, 3550, 453,
                6875, 680, 79, 7800, 117.0, 2.4, 2, 2017
            ),
            "B737-800": AircraftSpec(
                "B737-800", "Boeing", AircraftCategory.NARROW_BODY, 162, 21.1, 2935, 447,
                6875, 720, 79, 7800, 89.0, 2.6, 2, 1998
            ),
            
            # Wide Body
            "A330-900neo": AircraftSpec(
                "A330-900neo", "Airbus", AircraftCategory.WIDE_BODY, 287, 61.9, 7200, 470,
                36740, 1850, 242, 9200, 296.0, 2.0, 2, 2018
            ),
            "A350-900": AircraftSpec(
                "A350-900", "Airbus", AircraftCategory.WIDE_BODY, 315, 69.4, 8100, 488,
                37464, 1900, 280, 9000, 317.0, 1.8, 2, 2015
            ),
            "B777-300ER": AircraftSpec(
                "B777-300ER", "Boeing", AircraftCategory.WIDE_BODY, 396, 84.4, 7370, 490,
                47890, 2400, 351, 10400, 375.0, 2.2, 2, 2004
            ),
            "B787-9": AircraftSpec(
                "B787-9", "Boeing", AircraftCategory.WIDE_BODY, 290, 61.0, 7635, 488,
                33384, 1700, 254, 8400, 292.0, 1.9, 2, 2014
            ),
            
            # Cargo
            "B777F": AircraftSpec(
                "B777F", "Boeing", AircraftCategory.CARGO, 0, 103, 4970, 490,
                47890, 2400, 347, 10400, 352.0, 2.5, 2, 2009
            ),
            "A330-200F": AircraftSpec(
                "A330-200F", "Airbus", AircraftCategory.CARGO, 0, 70, 4000, 470,
                36740, 1850, 233, 8500, 241.0, 2.3, 2, 2010
            )
        }

    def get_spec(self, model: str) -> Optional[AircraftSpec]:
        return self.aircraft_specs.get(model)
    
    def get_specs_by_category(self, category: AircraftCategory) -> List[AircraftSpec]:
        return [spec for spec in self.aircraft_specs.values() if spec.category == category]

class AircraftMarketplace:
    """Main aircraft marketplace system"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.aircraft_db = AircraftDatabase()
        self.init_database()
        
    def init_database(self):
        """Initialize marketplace database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Market aircraft table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_aircraft (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                condition TEXT NOT NULL,
                age_years REAL NOT NULL,
                total_flight_hours INTEGER NOT NULL,
                cycles INTEGER NOT NULL,
                asking_price REAL NOT NULL,
                lease_rate_monthly REAL NOT NULL,
                seller_type TEXT NOT NULL,
                location TEXT NOT NULL,
                available_until TEXT NOT NULL,
                maintenance_due_hours INTEGER NOT NULL,
                financing_available TEXT NOT NULL,
                spec_data TEXT NOT NULL
            )
        ''')
        
        # Owned aircraft table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS owned_aircraft (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                condition TEXT NOT NULL,
                age_years REAL NOT NULL,
                total_flight_hours INTEGER NOT NULL,
                cycles INTEGER NOT NULL,
                purchase_price REAL NOT NULL,
                current_value REAL NOT NULL,
                financing_type TEXT NOT NULL,
                monthly_payment REAL NOT NULL,
                remaining_payments INTEGER NOT NULL,
                location TEXT NOT NULL,
                maintenance_due_hours INTEGER NOT NULL,
                last_maintenance TEXT NOT NULL,
                utilization_hours_month REAL NOT NULL,
                route_assignments TEXT NOT NULL,
                spec_data TEXT NOT NULL
            )
        ''')
        
        # Aircraft transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aircraft_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aircraft_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_market_aircraft(self, count: int = 50) -> List[MarketAircraft]:
        """Generate realistic market aircraft for sale/lease"""
        market_aircraft = []
        
        for _ in range(count):
            # Randomly select aircraft model
            model = random.choice(list(self.aircraft_db.aircraft_specs.keys()))
            spec = self.aircraft_db.get_spec(model)
            
            # Generate realistic aircraft characteristics
            age_years = random.uniform(0, 25)
            condition = self._determine_condition(age_years)
            
            # Flight hours based on age and utilization
            avg_annual_hours = random.uniform(2000, 4000)
            total_flight_hours = int(age_years * avg_annual_hours)
            
            # Cycles (roughly 1 cycle per 1.5 flight hours for short-haul, 1 per 8 hours for long-haul)
            if spec.category == AircraftCategory.REGIONAL:
                cycles = int(total_flight_hours / 1.2)
            elif spec.category == AircraftCategory.NARROW_BODY:
                cycles = int(total_flight_hours / 2.0)
            else:
                cycles = int(total_flight_hours / 6.0)
            
            # Calculate depreciated value
            asking_price = self._calculate_market_value(spec, age_years, condition, total_flight_hours)
            
            # Lease rate (typically 0.8-1.2% of aircraft value per month)
            lease_rate_monthly = asking_price * random.uniform(0.008, 0.012)
            
            # Generate other attributes
            seller_type = random.choice(["manufacturer", "airline", "leasing_company"])
            location = random.choice(["JFK", "LAX", "LHR", "CDG", "FRA", "NRT", "SIN", "DXB"])
            available_until = datetime.now() + timedelta(days=random.randint(7, 90))
            
            # Maintenance due
            maintenance_due_hours = random.randint(100, 2000)
            
            # Available financing options
            financing_available = [FinancingType.CASH]
            if seller_type in ["manufacturer", "leasing_company"]:
                financing_available.extend([FinancingType.LEASE, FinancingType.LOAN])
            
            aircraft_id = f"{model.replace(' ', '_')}_{random.randint(1000, 9999)}"
            
            market_aircraft.append(MarketAircraft(
                id=aircraft_id,
                spec=spec,
                condition=condition,
                age_years=age_years,
                total_flight_hours=total_flight_hours,
                cycles=cycles,
                asking_price=asking_price,
                lease_rate_monthly=lease_rate_monthly,
                seller_type=seller_type,
                location=location,
                available_until=available_until,
                maintenance_due_hours=maintenance_due_hours,
                financing_available=financing_available
            ))
        
        return market_aircraft
    
    def _determine_condition(self, age_years: float) -> AircraftCondition:
        """Determine aircraft condition based on age and random factors"""
        if age_years < 2:
            return AircraftCondition.NEW
        elif age_years < 5:
            return random.choice([AircraftCondition.NEW, AircraftCondition.EXCELLENT])
        elif age_years < 10:
            return random.choice([AircraftCondition.EXCELLENT, AircraftCondition.GOOD])
        elif age_years < 20:
            return random.choice([AircraftCondition.GOOD, AircraftCondition.FAIR])
        else:
            return random.choice([AircraftCondition.FAIR, AircraftCondition.POOR])
    
    def _calculate_market_value(self, spec: AircraftSpec, age_years: float, 
                               condition: AircraftCondition, flight_hours: int) -> float:
        """Calculate realistic market value based on depreciation"""
        base_value = spec.base_price
        
        # Age depreciation (aircraft typically depreciate 3-5% per year)
        age_factor = (1 - 0.04) ** age_years
        
        # Condition factor
        condition_factors = {
            AircraftCondition.NEW: 1.0,
            AircraftCondition.EXCELLENT: 0.95,
            AircraftCondition.GOOD: 0.85,
            AircraftCondition.FAIR: 0.70,
            AircraftCondition.POOR: 0.50
        }
        
        # High utilization penalty
        expected_hours = age_years * 3000
        if flight_hours > expected_hours * 1.3:
            utilization_factor = 0.9
        elif flight_hours < expected_hours * 0.7:
            utilization_factor = 1.05  # Low utilization can be good
        else:
            utilization_factor = 1.0
        
        market_value = base_value * age_factor * condition_factors[condition] * utilization_factor
        
        # Add some market randomness
        market_value *= random.uniform(0.9, 1.1)
        
        return round(market_value, 2)
    
    def save_market_aircraft(self, aircraft_list: List[MarketAircraft]):
        """Save market aircraft to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing market
        cursor.execute("DELETE FROM market_aircraft")
        
        for aircraft in aircraft_list:
            cursor.execute('''
                INSERT INTO market_aircraft VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                aircraft.id,
                aircraft.spec.model,
                aircraft.condition.value,
                aircraft.age_years,
                aircraft.total_flight_hours,
                aircraft.cycles,
                aircraft.asking_price,
                aircraft.lease_rate_monthly,
                aircraft.seller_type,
                aircraft.location,
                aircraft.available_until.isoformat(),
                aircraft.maintenance_due_hours,
                json.dumps([f.value for f in aircraft.financing_available]),
                json.dumps(self._spec_to_dict(aircraft.spec))
            ))
        
        conn.commit()
        conn.close()
    
    def _spec_to_dict(self, spec: AircraftSpec) -> Dict:
        """Convert AircraftSpec to dictionary with enum values"""
        spec_dict = asdict(spec)
        # Convert enum to its value
        spec_dict['category'] = spec.category.value
        return spec_dict
    
    def _dict_to_spec(self, spec_dict: Dict) -> AircraftSpec:
        """Convert dictionary back to AircraftSpec with proper enum"""
        # Convert string back to enum
        spec_dict['category'] = AircraftCategory(spec_dict['category'])
        return AircraftSpec(**spec_dict)
    
    def get_market_aircraft(self, filters: Dict = None) -> List[MarketAircraft]:
        """Retrieve market aircraft with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM market_aircraft WHERE available_until > ?"
        params = [datetime.now().isoformat()]
        
        if filters:
            if 'category' in filters:
                query += " AND spec_data LIKE ?"
                params.append(f'%"category": "{filters["category"].value}"%')
            
            if 'max_price' in filters:
                query += " AND asking_price <= ?"
                params.append(filters['max_price'])
            
            if 'min_price' in filters:
                query += " AND asking_price >= ?"
                params.append(filters['min_price'])
            
            if 'max_age' in filters:
                query += " AND age_years <= ?"
                params.append(filters['max_age'])
            
            if 'location' in filters:
                query += " AND location = ?"
                params.append(filters['location'])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        aircraft_list = []
        for row in rows:
            spec_data = json.loads(row[13])
            spec = self._dict_to_spec(spec_data)
            
            aircraft = MarketAircraft(
                id=row[0],
                spec=spec,
                condition=AircraftCondition(row[2]),
                age_years=row[3],
                total_flight_hours=row[4],
                cycles=row[5],
                asking_price=row[6],
                lease_rate_monthly=row[7],
                seller_type=row[8],
                location=row[9],
                available_until=datetime.fromisoformat(row[10]),
                maintenance_due_hours=row[11],
                financing_available=[FinancingType(f) for f in json.loads(row[12])]
            )
            aircraft_list.append(aircraft)
        
        return aircraft_list
    
    def purchase_aircraft(self, aircraft_id: str, financing_type: FinancingType, 
                         down_payment: float = 0) -> Tuple[bool, str, OwnedAircraft]:
        """Purchase an aircraft from the marketplace"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get aircraft from market
        cursor.execute("SELECT * FROM market_aircraft WHERE id = ?", (aircraft_id,))
        row = cursor.fetchone()
        
        if not row:
            return False, "Aircraft not found in marketplace", None
        
        # Check airline's current cash balance
        cursor.execute("SELECT cash_balance FROM airline_finances ORDER BY date DESC LIMIT 1")
        balance_row = cursor.fetchone()
        current_cash = balance_row[0] if balance_row else 0
        
        # Create MarketAircraft object
        spec_data = json.loads(row[13])
        spec = self._dict_to_spec(spec_data)
        market_aircraft = MarketAircraft(
            id=row[0], spec=spec, condition=AircraftCondition(row[2]),
            age_years=row[3], total_flight_hours=row[4], cycles=row[5],
            asking_price=row[6], lease_rate_monthly=row[7], seller_type=row[8],
            location=row[9], available_until=datetime.fromisoformat(row[10]),
            maintenance_due_hours=row[11],
            financing_available=[FinancingType(f) for f in json.loads(row[12])]
        )
        
        # Check if financing type is available
        if financing_type not in market_aircraft.financing_available:
            return False, f"Financing type {financing_type.value} not available for this aircraft", None
        
        # Calculate financing terms
        monthly_payment = 0
        remaining_payments = 0
        purchase_price = market_aircraft.asking_price
        upfront_cost = 0  # Amount needed immediately
        
        if financing_type == FinancingType.LEASE:
            monthly_payment = market_aircraft.lease_rate_monthly
            remaining_payments = 120  # 10 year lease
            purchase_price = 0  # No upfront cost for lease
            upfront_cost = 0  # Leases typically have no upfront cost
        elif financing_type == FinancingType.LOAN:
            loan_amount = purchase_price - down_payment
            interest_rate = 0.05 / 12  # 5% annual rate
            remaining_payments = 240  # 20 year loan
            upfront_cost = down_payment  # Down payment required
            if loan_amount > 0:
                monthly_payment = loan_amount * (interest_rate * (1 + interest_rate)**remaining_payments) / ((1 + interest_rate)**remaining_payments - 1)
        elif financing_type == FinancingType.CASH:
            upfront_cost = purchase_price  # Full amount needed upfront
        
        # Check if airline has sufficient cash
        if upfront_cost > current_cash:
            return False, f"Insufficient funds. Need ${upfront_cost:.1f}M but only have ${current_cash:.1f}M available.", None
        
        # Create owned aircraft
        owned_aircraft = OwnedAircraft(
            id=aircraft_id,
            spec=spec,
            condition=market_aircraft.condition,
            age_years=market_aircraft.age_years,
            total_flight_hours=market_aircraft.total_flight_hours,
            cycles=market_aircraft.cycles,
            purchase_price=purchase_price if financing_type != FinancingType.LEASE else market_aircraft.asking_price,
            current_value=market_aircraft.asking_price,
            financing_type=financing_type,
            monthly_payment=monthly_payment,
            remaining_payments=remaining_payments,
            location=market_aircraft.location,
            maintenance_due_hours=market_aircraft.maintenance_due_hours,
            last_maintenance=datetime.now() - timedelta(days=30),  # Assume recent maintenance
            utilization_hours_month=0,
            route_assignments=[]
        )
        
        # Save to owned aircraft table
        cursor.execute('''
            INSERT INTO owned_aircraft VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            owned_aircraft.id,
            owned_aircraft.spec.model,
            owned_aircraft.condition.value,
            owned_aircraft.age_years,
            owned_aircraft.total_flight_hours,
            owned_aircraft.cycles,
            owned_aircraft.purchase_price,
            owned_aircraft.current_value,
            owned_aircraft.financing_type.value,
            owned_aircraft.monthly_payment,
            owned_aircraft.remaining_payments,
            owned_aircraft.location,
            owned_aircraft.maintenance_due_hours,
            owned_aircraft.last_maintenance.isoformat(),
            owned_aircraft.utilization_hours_month,
            json.dumps(owned_aircraft.route_assignments),
            json.dumps(self._spec_to_dict(owned_aircraft.spec))
        ))
        
        # Record transaction
        cursor.execute('''
            INSERT INTO aircraft_transactions (aircraft_id, transaction_type, amount, transaction_date, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            aircraft_id,
            f"purchase_{financing_type.value}",
            purchase_price if financing_type != FinancingType.LEASE else monthly_payment,
            datetime.now().isoformat(),
            json.dumps({
                "financing_type": financing_type.value,
                "monthly_payment": monthly_payment,
                "down_payment": down_payment
            })
        ))
        
        # Remove from market
        cursor.execute("DELETE FROM market_aircraft WHERE id = ?", (aircraft_id,))
        
        # Update airline's cash balance
        new_cash_balance = current_cash - upfront_cost
        cursor.execute('''
            INSERT INTO airline_finances (date, cash_balance, revenue, expenses, profit_loss, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            new_cash_balance,
            0,  # No revenue from this transaction
            upfront_cost,  # This is an expense
            -upfront_cost,  # Negative profit (expense)
            f"Aircraft purchase: {aircraft_id} via {financing_type.value}"
        ))
        
        conn.commit()
        conn.close()
        
        return True, f"Aircraft purchased successfully! New cash balance: ${new_cash_balance:.1f}M", owned_aircraft
    
    def get_owned_aircraft(self) -> List[OwnedAircraft]:
        """Get all owned aircraft"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM owned_aircraft")
        rows = cursor.fetchall()
        conn.close()
        
        aircraft_list = []
        for row in rows:
            spec_data = json.loads(row[16])
            spec = self._dict_to_spec(spec_data)
            
            aircraft = OwnedAircraft(
                id=row[0],
                spec=spec,
                condition=AircraftCondition(row[2]),
                age_years=row[3],
                total_flight_hours=row[4],
                cycles=row[5],
                purchase_price=row[6],
                current_value=row[7],
                financing_type=FinancingType(row[8]),
                monthly_payment=row[9],
                remaining_payments=row[10],
                location=row[11],
                maintenance_due_hours=row[12],
                last_maintenance=datetime.fromisoformat(row[13]),
                utilization_hours_month=row[14],
                route_assignments=json.loads(row[15])
            )
            aircraft_list.append(aircraft)
        
        return aircraft_list
    
    def calculate_monthly_costs(self) -> Dict[str, float]:
        """Calculate total monthly aircraft-related costs"""
        owned_aircraft = self.get_owned_aircraft()
        
        total_payments = sum(aircraft.monthly_payment for aircraft in owned_aircraft)
        total_maintenance = sum(aircraft.current_value * aircraft.spec.annual_maintenance_cost / 12 
                             for aircraft in owned_aircraft)
        
        return {
            "financing_payments": total_payments,
            "maintenance_costs": total_maintenance,
            "total_monthly": total_payments + total_maintenance
        }
    
    def get_current_cash_balance(self) -> float:
        """Get the airline's current cash balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT cash_balance FROM airline_finances ORDER BY date DESC LIMIT 1")
        balance_row = cursor.fetchone()
        conn.close()
        
        return balance_row[0] if balance_row else 0.0


# Example usage and testing
if __name__ == "__main__":
    # Initialize marketplace
    marketplace = AircraftMarketplace("airline_game.db")
    
    # Generate market aircraft
    market_aircraft = marketplace.generate_market_aircraft(30)
    marketplace.save_market_aircraft(market_aircraft)
    
    # Display some market aircraft
    print("=== Aircraft Marketplace ===")
    available = marketplace.get_market_aircraft()
    for aircraft in available[:10]:  # Show first 10
        print(f"{aircraft.spec.model} ({aircraft.age_years:.1f} years)")
        print(f"  Price: ${aircraft.asking_price:.1f}M | Lease: ${aircraft.lease_rate_monthly:.0f}k/month")
        print(f"  Condition: {aircraft.condition.value} | Location: {aircraft.location}")
        print(f"  Capacity: {aircraft.spec.passenger_capacity} pax | Range: {aircraft.spec.max_range} nm")
        print()
    
    # Example purchase
    if available:
        aircraft_to_buy = available[0]
        success, message, owned = marketplace.purchase_aircraft(
            aircraft_to_buy.id, 
            FinancingType.LOAN, 
            down_payment=aircraft_to_buy.asking_price * 0.2
        )
        
        if success:
            print(f"Successfully purchased {owned.spec.model}!")
            print(f"Monthly payment: ${owned.monthly_payment:.0f}k")
        else:
            print(f"Purchase failed: {message}")
    
    # Show monthly costs
    costs = marketplace.calculate_monthly_costs()
    print(f"\nMonthly Aircraft Costs:")
    print(f"Financing: ${costs['financing_payments']:.0f}k")
    print(f"Maintenance: ${costs['maintenance_costs']:.0f}k")
    print(f"Total: ${costs['total_monthly']:.0f}k")