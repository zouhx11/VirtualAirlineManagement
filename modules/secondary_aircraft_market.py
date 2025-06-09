import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from core.config_manager import ConfigManager


class ListingType(Enum):
    """Types of aircraft listings."""
    SALE = "sale"
    LEASE = "lease"
    SALE_LEASEBACK = "sale_leaseback"
    AUCTION = "auction"


class ListingStatus(Enum):
    """Status of aircraft listings."""
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class AircraftListing:
    """Aircraft listing in secondary market."""
    listing_id: int
    aircraft_id: int
    seller_airline_id: int
    seller_airline_name: str
    aircraft_type: str
    registration: str
    age_years: float
    total_hours: int
    condition: str
    asking_price: float
    market_value: float
    listing_type: ListingType
    lease_rate_monthly: Optional[float]
    lease_term_months: Optional[int]
    listing_date: datetime
    expiry_date: datetime
    status: ListingStatus
    description: str
    negotiable: bool
    minimum_price: Optional[float]
    images: List[str]
    maintenance_records: str
    special_features: List[str]


@dataclass
class MarketTransaction:
    """Record of completed aircraft transaction."""
    transaction_id: int
    listing_id: int
    buyer_airline_id: int
    seller_airline_id: int
    aircraft_id: int
    transaction_type: str
    agreed_price: float
    transaction_date: datetime
    financing_method: str
    commission: float


class SecondaryAircraftMarket:
    """Secondary aircraft market for airline-to-airline transactions."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.commission_rate = 0.03  # 3% commission on transactions
        self.initialize_market_tables()
    
    def initialize_market_tables(self):
        """Initialize secondary market database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Aircraft listings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS aircraft_listings (
                        listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        aircraft_id INTEGER,
                        seller_airline_id INTEGER,
                        seller_airline_name TEXT,
                        aircraft_type TEXT,
                        registration TEXT,
                        age_years REAL,
                        total_hours INTEGER,
                        condition TEXT,
                        asking_price REAL,
                        market_value REAL,
                        listing_type TEXT,
                        lease_rate_monthly REAL,
                        lease_term_months INTEGER,
                        listing_date TEXT,
                        expiry_date TEXT,
                        status TEXT,
                        description TEXT,
                        negotiable BOOLEAN,
                        minimum_price REAL,
                        maintenance_records TEXT,
                        special_features TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (aircraft_id) REFERENCES aircraft (id),
                        FOREIGN KEY (seller_airline_id) REFERENCES airlines (id)
                    )
                """)
                
                # Market transactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_transactions (
                        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        listing_id INTEGER,
                        buyer_airline_id INTEGER,
                        seller_airline_id INTEGER,
                        aircraft_id INTEGER,
                        transaction_type TEXT,
                        agreed_price REAL,
                        transaction_date TEXT,
                        financing_method TEXT,
                        commission REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (listing_id) REFERENCES aircraft_listings (listing_id),
                        FOREIGN KEY (aircraft_id) REFERENCES aircraft (id)
                    )
                """)
                
                # Market valuations table (for pricing reference)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS aircraft_valuations (
                        valuation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        aircraft_type TEXT,
                        age_years REAL,
                        total_hours INTEGER,
                        condition TEXT,
                        base_value REAL,
                        market_multiplier REAL,
                        valuation_date TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"Error initializing market tables: {e}")
    
    def create_listing(self, aircraft_id: int, seller_airline_id: int, 
                      listing_type: ListingType, asking_price: float,
                      **kwargs) -> Optional[int]:
        """Create a new aircraft listing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get aircraft details
                cursor.execute("""
                    SELECT a.aircraft_type, a.registration, a.age_years, 
                           a.total_flight_hours, a.condition, a.current_value,
                           al.name as airline_name
                    FROM aircraft a
                    LEFT JOIN airlines al ON a.airline_id = al.id
                    WHERE a.id = ? AND a.airline_id = ?
                """, (aircraft_id, seller_airline_id))
                
                aircraft_data = cursor.fetchone()
                if not aircraft_data:
                    return None
                
                # Calculate market value
                market_value = self.calculate_market_value(
                    aircraft_data[0], aircraft_data[2], aircraft_data[3], aircraft_data[4]
                )
                
                # Set expiry date (30 days from now)
                listing_date = datetime.now()
                expiry_date = listing_date + timedelta(days=30)
                
                # Insert listing
                cursor.execute("""
                    INSERT INTO aircraft_listings (
                        aircraft_id, seller_airline_id, seller_airline_name,
                        aircraft_type, registration, age_years, total_hours,
                        condition, asking_price, market_value, listing_type,
                        lease_rate_monthly, lease_term_months, listing_date,
                        expiry_date, status, description, negotiable,
                        minimum_price, maintenance_records, special_features
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    aircraft_id, seller_airline_id, aircraft_data[6],
                    aircraft_data[0], aircraft_data[1], aircraft_data[2],
                    aircraft_data[3], aircraft_data[4], asking_price,
                    market_value, listing_type.value,
                    kwargs.get('lease_rate_monthly'),
                    kwargs.get('lease_term_months'),
                    listing_date.isoformat(),
                    expiry_date.isoformat(),
                    ListingStatus.ACTIVE.value,
                    kwargs.get('description', ''),
                    kwargs.get('negotiable', True),
                    kwargs.get('minimum_price'),
                    kwargs.get('maintenance_records', ''),
                    ','.join(kwargs.get('special_features', []))
                ))
                
                listing_id = cursor.lastrowid
                
                # Update aircraft status to "For Sale"
                cursor.execute("""
                    UPDATE aircraft SET status = 'For Sale' WHERE id = ?
                """, (aircraft_id,))
                
                conn.commit()
                return listing_id
                
        except Exception as e:
            print(f"Error creating listing: {e}")
            return None
    
    def get_active_listings(self, exclude_airline_id: Optional[int] = None) -> List[AircraftListing]:
        """Get all active aircraft listings."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT listing_id, aircraft_id, seller_airline_id, seller_airline_name,
                           aircraft_type, registration, age_years, total_hours, condition,
                           asking_price, market_value, listing_type, lease_rate_monthly,
                           lease_term_months, listing_date, expiry_date, status,
                           description, negotiable, minimum_price, maintenance_records,
                           special_features
                    FROM aircraft_listings
                    WHERE status = 'active' AND expiry_date > ?
                """
                
                params = [datetime.now().isoformat()]
                
                if exclude_airline_id:
                    query += " AND seller_airline_id != ?"
                    params.append(exclude_airline_id)
                
                query += " ORDER BY listing_date DESC"
                
                cursor.execute(query, params)
                listings_data = cursor.fetchall()
                
                listings = []
                for row in listings_data:
                    listing = AircraftListing(
                        listing_id=row[0],
                        aircraft_id=row[1],
                        seller_airline_id=row[2],
                        seller_airline_name=row[3],
                        aircraft_type=row[4],
                        registration=row[5],
                        age_years=row[6],
                        total_hours=row[7],
                        condition=row[8],
                        asking_price=row[9],
                        market_value=row[10],
                        listing_type=ListingType(row[11]),
                        lease_rate_monthly=row[12],
                        lease_term_months=row[13],
                        listing_date=datetime.fromisoformat(row[14]),
                        expiry_date=datetime.fromisoformat(row[15]),
                        status=ListingStatus(row[16]),
                        description=row[17],
                        negotiable=bool(row[18]),
                        minimum_price=row[19],
                        images=[],  # Would be populated from separate images table
                        maintenance_records=row[20],
                        special_features=row[21].split(',') if row[21] else []
                    )
                    listings.append(listing)
                
                return listings
                
        except Exception as e:
            print(f"Error getting listings: {e}")
            return []
    
    def calculate_market_value(self, aircraft_type: str, age_years: float, 
                             total_hours: int, condition: str) -> float:
        """Calculate current market value of aircraft."""
        # Base values for different aircraft types (in millions)
        base_values = {
            "A320neo": 110.0,
            "A321neo": 130.0,
            "A330-900neo": 290.0,
            "A350-900": 320.0,
            "A380": 450.0,
            "B737 MAX 8": 120.0,
            "B737 MAX 9": 130.0,
            "B787-8": 250.0,
            "B787-9": 290.0,
            "B777-300ER": 370.0,
            "B747-8F": 420.0,
            "E190": 50.0
        }
        
        base_value = base_values.get(aircraft_type, 100.0) * 1_000_000
        
        # Age depreciation (4% per year, but market conditions can vary)
        age_factor = max(0.2, 1 - (age_years * 0.04))
        
        # Hours depreciation (high-time aircraft worth less)
        max_hours = {"narrow": 100000, "wide": 120000, "regional": 80000}
        aircraft_category = self.get_aircraft_category(aircraft_type)
        hours_factor = max(0.5, 1 - (total_hours / max_hours.get(aircraft_category, 100000)))
        
        # Condition factor
        condition_multipliers = {
            "Excellent": 1.1,
            "Good": 1.0,
            "Fair": 0.85,
            "Poor": 0.7
        }
        condition_factor = condition_multipliers.get(condition, 1.0)
        
        # Market conditions (random fluctuation ±15%)
        market_factor = random.uniform(0.85, 1.15)
        
        market_value = base_value * age_factor * hours_factor * condition_factor * market_factor
        
        return round(market_value, -4)  # Round to nearest $10k
    
    def get_aircraft_category(self, aircraft_type: str) -> str:
        """Get aircraft category for valuation purposes."""
        narrow_body = ["A320neo", "A321neo", "B737 MAX 8", "B737 MAX 9"]
        wide_body = ["A330-900neo", "A350-900", "A380", "B787-8", "B787-9", "B777-300ER", "B747-8F"]
        regional = ["E190"]
        
        if aircraft_type in narrow_body:
            return "narrow"
        elif aircraft_type in wide_body:
            return "wide"
        elif aircraft_type in regional:
            return "regional"
        else:
            return "narrow"
    
    def make_offer(self, listing_id: int, buyer_airline_id: int, 
                   offer_price: float, financing_method: str = "cash") -> bool:
        """Make an offer on an aircraft listing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get listing details
                cursor.execute("""
                    SELECT asking_price, minimum_price, negotiable, seller_airline_id,
                           aircraft_id, listing_type
                    FROM aircraft_listings
                    WHERE listing_id = ? AND status = 'active'
                """, (listing_id,))
                
                listing_data = cursor.fetchone()
                if not listing_data:
                    return False
                
                asking_price, minimum_price, negotiable, seller_id, aircraft_id, listing_type = listing_data
                
                # Check if offer is acceptable
                min_acceptable = minimum_price if minimum_price else asking_price * 0.8
                
                if offer_price >= asking_price:
                    # Offer accepted immediately
                    return self.execute_transaction(
                        listing_id, buyer_airline_id, seller_id, aircraft_id,
                        offer_price, financing_method, ListingType(listing_type)
                    )
                elif negotiable and offer_price >= min_acceptable:
                    # Counteroffer logic (simplified - auto-accept if reasonable)
                    counter_price = min(asking_price, offer_price * 1.05)
                    return self.execute_transaction(
                        listing_id, buyer_airline_id, seller_id, aircraft_id,
                        counter_price, financing_method, ListingType(listing_type)
                    )
                else:
                    # Offer rejected
                    return False
                    
        except Exception as e:
            print(f"Error making offer: {e}")
            return False
    
    def execute_transaction(self, listing_id: int, buyer_airline_id: int,
                          seller_airline_id: int, aircraft_id: int,
                          agreed_price: float, financing_method: str,
                          transaction_type: ListingType) -> bool:
        """Execute the aircraft transaction."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate commission
                commission = agreed_price * self.commission_rate
                seller_proceeds = agreed_price - commission
                
                # Record transaction
                cursor.execute("""
                    INSERT INTO market_transactions (
                        listing_id, buyer_airline_id, seller_airline_id,
                        aircraft_id, transaction_type, agreed_price,
                        transaction_date, financing_method, commission
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    listing_id, buyer_airline_id, seller_airline_id,
                    aircraft_id, transaction_type.value, agreed_price,
                    datetime.now().isoformat(), financing_method, commission
                ))
                
                if transaction_type == ListingType.SALE:
                    # Transfer aircraft ownership
                    cursor.execute("""
                        UPDATE aircraft 
                        SET airline_id = ?, status = 'Active', purchase_price = ?,
                            current_value = ?
                        WHERE id = ?
                    """, (buyer_airline_id, agreed_price, agreed_price, aircraft_id))
                    
                    # Update seller's cash (add proceeds)
                    cursor.execute("""
                        UPDATE airlines 
                        SET cash_balance = cash_balance + ?
                        WHERE id = ?
                    """, (seller_proceeds, seller_airline_id))
                    
                    # Update buyer's cash (subtract payment)
                    cursor.execute("""
                        UPDATE airlines 
                        SET cash_balance = cash_balance - ?
                        WHERE id = ?
                    """, (agreed_price, buyer_airline_id))
                
                elif transaction_type == ListingType.LEASE:
                    # Set up lease arrangement
                    cursor.execute("""
                        UPDATE aircraft 
                        SET status = 'Leased', airline_id = ?
                        WHERE id = ?
                    """, (buyer_airline_id, aircraft_id))
                
                # Mark listing as sold
                cursor.execute("""
                    UPDATE aircraft_listings 
                    SET status = 'sold'
                    WHERE listing_id = ?
                """, (listing_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error executing transaction: {e}")
            return False
    
    def get_market_statistics(self) -> Dict:
        """Get market statistics and trends."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Active listings count
                cursor.execute("""
                    SELECT COUNT(*) FROM aircraft_listings 
                    WHERE status = 'active'
                """)
                active_listings = cursor.fetchone()[0]
                
                # Recent transactions (last 30 days)
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*), AVG(agreed_price)
                    FROM market_transactions
                    WHERE transaction_date > ?
                """, (thirty_days_ago,))
                
                recent_data = cursor.fetchone()
                recent_transactions = recent_data[0]
                avg_transaction_value = recent_data[1] or 0
                
                # Price trends by aircraft type
                cursor.execute("""
                    SELECT al.aircraft_type, AVG(mt.agreed_price), COUNT(*)
                    FROM market_transactions mt
                    JOIN aircraft_listings al ON mt.listing_id = al.listing_id
                    WHERE mt.transaction_date > ?
                    GROUP BY al.aircraft_type
                    ORDER BY AVG(mt.agreed_price) DESC
                """, (thirty_days_ago,))
                
                price_trends = cursor.fetchall()
                
                # Market volume
                cursor.execute("""
                    SELECT SUM(agreed_price) FROM market_transactions
                    WHERE transaction_date > ?
                """, (thirty_days_ago,))
                
                market_volume = cursor.fetchone()[0] or 0
                
                return {
                    "active_listings": active_listings,
                    "recent_transactions": recent_transactions,
                    "avg_transaction_value": avg_transaction_value,
                    "market_volume": market_volume,
                    "price_trends": [
                        {"aircraft_type": row[0], "avg_price": row[1], "count": row[2]}
                        for row in price_trends
                    ]
                }
                
        except Exception as e:
            print(f"Error getting market statistics: {e}")
            return {}
    
    def get_similar_aircraft_prices(self, aircraft_type: str, age_years: float) -> List[float]:
        """Get recent sale prices for similar aircraft."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find similar aircraft sales (same type, similar age ±2 years)
                cursor.execute("""
                    SELECT mt.agreed_price
                    FROM market_transactions mt
                    JOIN aircraft_listings al ON mt.listing_id = al.listing_id
                    WHERE al.aircraft_type = ? 
                    AND al.age_years BETWEEN ? AND ?
                    AND mt.transaction_date > ?
                    ORDER BY mt.transaction_date DESC
                    LIMIT 10
                """, (
                    aircraft_type, 
                    age_years - 2, 
                    age_years + 2,
                    (datetime.now() - timedelta(days=180)).isoformat()
                ))
                
                prices = [row[0] for row in cursor.fetchall()]
                return prices
                
        except Exception as e:
            print(f"Error getting similar aircraft prices: {e}")
            return []
    
    def cancel_listing(self, listing_id: int, seller_airline_id: int) -> bool:
        """Cancel an aircraft listing."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update listing status
                cursor.execute("""
                    UPDATE aircraft_listings 
                    SET status = 'cancelled'
                    WHERE listing_id = ? AND seller_airline_id = ?
                """, (listing_id, seller_airline_id))
                
                # Get aircraft ID to update status
                cursor.execute("""
                    SELECT aircraft_id FROM aircraft_listings
                    WHERE listing_id = ?
                """, (listing_id,))
                
                aircraft_id = cursor.fetchone()
                if aircraft_id:
                    # Update aircraft status back to Active
                    cursor.execute("""
                        UPDATE aircraft 
                        SET status = 'Active'
                        WHERE id = ?
                    """, (aircraft_id[0],))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error cancelling listing: {e}")
            return False
    
    def get_airline_listings(self, airline_id: int) -> List[AircraftListing]:
        """Get all listings for a specific airline."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT listing_id, aircraft_id, seller_airline_id, seller_airline_name,
                           aircraft_type, registration, age_years, total_hours, condition,
                           asking_price, market_value, listing_type, lease_rate_monthly,
                           lease_term_months, listing_date, expiry_date, status,
                           description, negotiable, minimum_price, maintenance_records,
                           special_features
                    FROM aircraft_listings
                    WHERE seller_airline_id = ?
                    ORDER BY listing_date DESC
                """, (airline_id,))
                
                listings_data = cursor.fetchall()
                
                listings = []
                for row in listings_data:
                    listing = AircraftListing(
                        listing_id=row[0],
                        aircraft_id=row[1],
                        seller_airline_id=row[2],
                        seller_airline_name=row[3],
                        aircraft_type=row[4],
                        registration=row[5],
                        age_years=row[6],
                        total_hours=row[7],
                        condition=row[8],
                        asking_price=row[9],
                        market_value=row[10],
                        listing_type=ListingType(row[11]),
                        lease_rate_monthly=row[12],
                        lease_term_months=row[13],
                        listing_date=datetime.fromisoformat(row[14]),
                        expiry_date=datetime.fromisoformat(row[15]),
                        status=ListingStatus(row[16]),
                        description=row[17],
                        negotiable=bool(row[18]),
                        minimum_price=row[19],
                        images=[],
                        maintenance_records=row[20],
                        special_features=row[21].split(',') if row[21] else []
                    )
                    listings.append(listing)
                
                return listings
                
        except Exception as e:
            print(f"Error getting airline listings: {e}")
            return []