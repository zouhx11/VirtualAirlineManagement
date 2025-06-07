# modules/aircraft_marketplace_gui.py - TTKBootstrap Compatible Version

import ttkbootstrap as ttk
from ttkbootstrap.constants import SUCCESS, INFO, WARNING, PRIMARY, SECONDARY, DANGER
from ttkbootstrap.dialogs import Messagebox
from tkinter import simpledialog
from typing import List, Dict, Optional
import threading
from datetime import datetime

from .aircraft_marketplace import (
    AircraftMarketplace, MarketAircraft, OwnedAircraft, 
    AircraftCategory, AircraftCondition, FinancingType
)

class AircraftMarketplaceGUI:
    """TTKBootstrap compatible GUI for the aircraft marketplace system"""
    
    def __init__(self, parent_notebook: ttk.Notebook, db_path: str):
        self.marketplace = AircraftMarketplace(db_path)
        self.parent_notebook = parent_notebook
        
        # Create main frames
        self.create_marketplace_tab()
        self.create_fleet_tab()
        
        # Load initial data
        self.refresh_market_data()
    
    def create_marketplace_tab(self):
        """Create the aircraft marketplace tab"""
        # Main marketplace frame
        self.marketplace_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.marketplace_frame, text="🛩️ Aircraft Market")
        
        # Create paned window for layout
        paned_window = ttk.PanedWindow(self.marketplace_frame, orient='horizontal')
        paned_window.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - filters and search
        left_frame = ttk.LabelFrame(paned_window, text="Search & Filters", width=300)
        paned_window.add(left_frame)
        
        # Search filters
        ttk.Label(left_frame, text="Aircraft Category:").pack(anchor='w', padx=5, pady=2)
        self.category_var = ttk.StringVar(value="All")
        category_combo = ttk.Combobox(left_frame, textvariable=self.category_var, width=25)
        category_combo['values'] = ["All"] + [cat.value.replace("_", " ").title() for cat in AircraftCategory]
        category_combo.pack(padx=5, pady=2, fill='x')
        
        ttk.Label(left_frame, text="Max Price ($ Million):").pack(anchor='w', padx=5, pady=2)
        self.max_price_var = ttk.StringVar()
        ttk.Entry(left_frame, textvariable=self.max_price_var, width=25).pack(padx=5, pady=2, fill='x')
        
        ttk.Label(left_frame, text="Max Age (Years):").pack(anchor='w', padx=5, pady=2)
        self.max_age_var = ttk.StringVar()
        ttk.Entry(left_frame, textvariable=self.max_age_var, width=25).pack(padx=5, pady=2, fill='x')
        
        ttk.Label(left_frame, text="Location:").pack(anchor='w', padx=5, pady=2)
        self.location_var = ttk.StringVar()
        location_combo = ttk.Combobox(left_frame, textvariable=self.location_var, width=25)
        location_combo['values'] = ["All", "JFK", "LAX", "LHR", "CDG", "FRA", "NRT", "SIN", "DXB"]
        location_combo.pack(padx=5, pady=2, fill='x')
        
        # Search button
        ttk.Button(left_frame, text="🔍 Search Aircraft", bootstyle=PRIMARY,
                  command=self.search_aircraft).pack(padx=5, pady=10, fill='x')
        
        # Generate new market button
        ttk.Button(left_frame, text="🔄 Refresh Market", bootstyle=INFO,
                  command=self.refresh_market_data).pack(padx=5, pady=5, fill='x')
        
        # Aircraft details frame
        details_frame = ttk.LabelFrame(left_frame, text="Aircraft Details")
        details_frame.pack(fill='both', expand=True, padx=5, pady=10)
        
        self.details_text = ttk.Text(details_frame, wrap='word', height=15, width=35)
        details_scrollbar = ttk.Scrollbar(details_frame, orient='vertical', command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side='left', fill='both', expand=True)
        details_scrollbar.pack(side='right', fill='y')
        
        # Right panel - aircraft listings
        right_frame = ttk.LabelFrame(paned_window, text="Available Aircraft")
        paned_window.add(right_frame)
        
        # Aircraft treeview
        columns = ("Model", "Age", "Price", "Lease", "Condition", "Location", "Pax", "Range")
        self.market_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        # Configure columns
        self.market_tree.heading("Model", text="Aircraft Model")
        self.market_tree.heading("Age", text="Age (Y)")
        self.market_tree.heading("Price", text="Price ($M)")
        self.market_tree.heading("Lease", text="Lease ($/M)")
        self.market_tree.heading("Condition", text="Condition")
        self.market_tree.heading("Location", text="Location")
        self.market_tree.heading("Pax", text="Passengers")
        self.market_tree.heading("Range", text="Range (NM)")
        
        self.market_tree.column("Model", width=150)
        self.market_tree.column("Age", width=60)
        self.market_tree.column("Price", width=80)
        self.market_tree.column("Lease", width=80)
        self.market_tree.column("Condition", width=80)
        self.market_tree.column("Location", width=70)
        self.market_tree.column("Pax", width=70)
        self.market_tree.column("Range", width=80)
        
        # Treeview scrollbar
        market_scrollbar = ttk.Scrollbar(right_frame, orient='vertical', command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=market_scrollbar.set)
        
        self.market_tree.pack(side='left', fill='both', expand=True)
        market_scrollbar.pack(side='right', fill='y')
        
        # Bind selection event
        self.market_tree.bind("<<TreeviewSelect>>", self.on_aircraft_select)
        
        # Purchase buttons frame
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="💰 Buy Cash", bootstyle=SUCCESS,
                  command=lambda: self.purchase_aircraft(FinancingType.CASH)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🏦 Finance Loan", bootstyle=WARNING,
                  command=lambda: self.purchase_aircraft(FinancingType.LOAN)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📄 Lease", bootstyle=INFO,
                  command=lambda: self.purchase_aircraft(FinancingType.LEASE)).pack(side='left', padx=5)
    
    def create_fleet_tab(self):
        """Create the owned fleet management tab"""
        self.fleet_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.fleet_frame, text="✈️ My Fleet")
        
        # Create paned window
        fleet_paned = ttk.PanedWindow(self.fleet_frame, orient='horizontal')
        fleet_paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - fleet summary
        left_fleet_frame = ttk.LabelFrame(fleet_paned, text="Fleet Summary", width=300)
        fleet_paned.add(left_fleet_frame)
        
        # Fleet statistics
        self.fleet_stats_text = ttk.Text(left_fleet_frame, wrap='word', height=15, width=35)
        fleet_stats_scrollbar = ttk.Scrollbar(left_fleet_frame, orient='vertical', command=self.fleet_stats_text.yview)
        self.fleet_stats_text.configure(yscrollcommand=fleet_stats_scrollbar.set)
        
        self.fleet_stats_text.pack(side='left', fill='both', expand=True)
        fleet_stats_scrollbar.pack(side='right', fill='y')
        
        # Right panel - owned aircraft
        right_fleet_frame = ttk.LabelFrame(fleet_paned, text="Owned Aircraft")
        fleet_paned.add(right_fleet_frame)
        
        # Owned aircraft treeview
        fleet_columns = ("Model", "Age", "Value", "Payment", "Condition", "Location", "Hours", "Routes")
        self.fleet_tree = ttk.Treeview(right_fleet_frame, columns=fleet_columns, show="headings", height=20)
        
        # Configure fleet columns
        self.fleet_tree.heading("Model", text="Aircraft Model")
        self.fleet_tree.heading("Age", text="Age (Y)")
        self.fleet_tree.heading("Value", text="Value ($M)")
        self.fleet_tree.heading("Payment", text="Payment ($/M)")
        self.fleet_tree.heading("Condition", text="Condition")
        self.fleet_tree.heading("Location", text="Location")
        self.fleet_tree.heading("Hours", text="Flight Hours")
        self.fleet_tree.heading("Routes", text="Routes")
        
        self.fleet_tree.column("Model", width=150)
        self.fleet_tree.column("Age", width=60)
        self.fleet_tree.column("Value", width=80)
        self.fleet_tree.column("Payment", width=80)
        self.fleet_tree.column("Condition", width=80)
        self.fleet_tree.column("Location", width=70)
        self.fleet_tree.column("Hours", width=80)
        self.fleet_tree.column("Routes", width=60)
        
        # Fleet treeview scrollbar
        fleet_tree_scrollbar = ttk.Scrollbar(right_fleet_frame, orient='vertical', command=self.fleet_tree.yview)
        self.fleet_tree.configure(yscrollcommand=fleet_tree_scrollbar.set)
        
        self.fleet_tree.pack(side='left', fill='both', expand=True)
        fleet_tree_scrollbar.pack(side='right', fill='y')
        
        # Fleet management buttons
        fleet_button_frame = ttk.Frame(right_fleet_frame)
        fleet_button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(fleet_button_frame, text="🗺️ Assign Route", bootstyle=PRIMARY,
                  command=self.assign_route).pack(side='left', padx=5)
        ttk.Button(fleet_button_frame, text="🔧 Schedule Maintenance", bootstyle=WARNING,
                  command=self.schedule_maintenance).pack(side='left', padx=5)
        ttk.Button(fleet_button_frame, text="💸 Sell Aircraft", bootstyle=DANGER,
                  command=self.sell_aircraft).pack(side='left', padx=5)
        ttk.Button(fleet_button_frame, text="🔄 Refresh Fleet", bootstyle=INFO,
                  command=self.refresh_fleet_data).pack(side='left', padx=5)
    
    def refresh_market_data(self):
        """Refresh market aircraft data"""
        def refresh_in_background():
            # Generate new market aircraft
            market_aircraft = self.marketplace.generate_market_aircraft(50)
            self.marketplace.save_market_aircraft(market_aircraft)
            
            # Update GUI in main thread
            self.marketplace_frame.after(0, self.load_market_aircraft)
        
        # Show loading message
        for item in self.market_tree.get_children():
            self.market_tree.delete(item)
        self.market_tree.insert("", 0, values=("Loading...", "", "", "", "", "", "", ""))
        
        # Run in background thread
        threading.Thread(target=refresh_in_background, daemon=True).start()
    
    def load_market_aircraft(self):
        """Load market aircraft into the treeview"""
        # Clear existing items
        for item in self.market_tree.get_children():
            self.market_tree.delete(item)
        
        # Get aircraft from marketplace
        try:
            aircraft_list = self.marketplace.get_market_aircraft()
            
            for aircraft in aircraft_list:
                values = (
                    aircraft.spec.model,
                    f"{aircraft.age_years:.1f}",
                    f"{aircraft.asking_price:.1f}",
                    f"{aircraft.lease_rate_monthly:.0f}k",
                    aircraft.condition.value.title(),
                    aircraft.location,
                    aircraft.spec.passenger_capacity,
                    f"{aircraft.spec.max_range:,}"
                )
                
                item_id = self.market_tree.insert("", 'end', values=values)
                # Store aircraft object for later retrieval
                self.market_tree.set(item_id, "aircraft_obj", aircraft)
        
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to load market data: {str(e)}")
    
    def search_aircraft(self):
        """Search aircraft based on filters"""
        filters = {}
        
        # Apply category filter
        if self.category_var.get() != "All":
            category_name = self.category_var.get().lower().replace(" ", "_")
            for cat in AircraftCategory:
                if cat.value == category_name:
                    filters['category'] = cat
                    break
        
        # Apply price filter
        if self.max_price_var.get():
            try:
                filters['max_price'] = float(self.max_price_var.get())
            except ValueError:
                Messagebox.show_error("Error", "Invalid max price value")
                return
        
        # Apply age filter
        if self.max_age_var.get():
            try:
                filters['max_age'] = float(self.max_age_var.get())
            except ValueError:
                Messagebox.show_error("Error", "Invalid max age value")
                return
        
        # Apply location filter
        if self.location_var.get() and self.location_var.get() != "All":
            filters['location'] = self.location_var.get()
        
        # Clear existing items
        for item in self.market_tree.get_children():
            self.market_tree.delete(item)
        
        # Load filtered aircraft
        try:
            aircraft_list = self.marketplace.get_market_aircraft(filters)
            
            for aircraft in aircraft_list:
                values = (
                    aircraft.spec.model,
                    f"{aircraft.age_years:.1f}",
                    f"{aircraft.asking_price:.1f}",
                    f"{aircraft.lease_rate_monthly:.0f}k",
                    aircraft.condition.value.title(),
                    aircraft.location,
                    aircraft.spec.passenger_capacity,
                    f"{aircraft.spec.max_range:,}"
                )
                
                item_id = self.market_tree.insert("", 'end', values=values)
                self.market_tree.set(item_id, "aircraft_obj", aircraft)
        
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to search aircraft: {str(e)}")
    
    def on_aircraft_select(self, event):
        """Handle aircraft selection in treeview"""
        selection = self.market_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        aircraft = self.market_tree.set(item, "aircraft_obj")
        
        if aircraft:
            self.display_aircraft_details(aircraft)
    
    def display_aircraft_details(self, aircraft: MarketAircraft):
        """Display detailed aircraft information"""
        self.details_text.delete(1.0, 'end')
        
        details = f"""AIRCRAFT DETAILS

Model: {aircraft.spec.model}
Manufacturer: {aircraft.spec.manufacturer}
Category: {aircraft.spec.category.value.replace('_', ' ').title()}

SPECIFICATIONS
Passenger Capacity: {aircraft.spec.passenger_capacity:,}
Cargo Capacity: {aircraft.spec.cargo_capacity:.1f} tons
Maximum Range: {aircraft.spec.max_range:,} nautical miles
Cruise Speed: {aircraft.spec.cruise_speed:,} knots
Fuel Capacity: {aircraft.spec.fuel_capacity:,} gallons
Fuel Burn: {aircraft.spec.fuel_burn_per_hour:.0f} gph
MTOW: {aircraft.spec.mtow:,} tons
Runway Required: {aircraft.spec.runway_length_required:,} feet
Crew Required: {aircraft.spec.crew_required}

AIRCRAFT CONDITION
Age: {aircraft.age_years:.1f} years
Condition: {aircraft.condition.value.title()}
Total Flight Hours: {aircraft.total_flight_hours:,}
Cycles: {aircraft.cycles:,}
Maintenance Due: {aircraft.maintenance_due_hours:,} hours

FINANCIAL
Asking Price: ${aircraft.asking_price:.2f} million
Monthly Lease: ${aircraft.lease_rate_monthly:.0f}k
Annual Maintenance: {aircraft.spec.annual_maintenance_cost:.1f}% of value
Seller: {aircraft.seller_type.replace('_', ' ').title()}

AVAILABILITY
Location: {aircraft.location}
Available Until: {aircraft.available_until.strftime('%Y-%m-%d')}
Financing Options: {', '.join([f.value.title() for f in aircraft.financing_available])}
"""
        
        self.details_text.insert(1.0, details)
    
    def purchase_aircraft(self, financing_type: FinancingType):
        """Purchase selected aircraft"""
        selection = self.market_tree.selection()
        if not selection:
            Messagebox.show_warning("No Selection", "Please select an aircraft to purchase.")
            return
        
        item = selection[0]
        aircraft = self.market_tree.set(item, "aircraft_obj")
        
        if not aircraft:
            Messagebox.show_error("Error", "Invalid aircraft selection.")
            return
        
        # Check if financing type is available
        if financing_type not in aircraft.financing_available:
            Messagebox.show_error("Financing Error", 
                               f"{financing_type.value.title()} financing not available for this aircraft.")
            return
        
        # Get down payment for loan financing
        down_payment = 0
        if financing_type == FinancingType.LOAN:
            down_payment_str = simpledialog.askstring(
                "Down Payment", 
                f"Enter down payment (% of ${aircraft.asking_price:.1f}M):\n(Recommended: 20%)",
                initialvalue="20"
            )
            if down_payment_str:
                try:
                    down_payment_pct = float(down_payment_str)
                    down_payment = aircraft.asking_price * (down_payment_pct / 100)
                except ValueError:
                    Messagebox.show_error("Error", "Invalid down payment percentage.")
                    return
            else:
                return  # User cancelled
        
        # Confirm purchase
        if financing_type == FinancingType.CASH:
            message = f"Purchase {aircraft.spec.model} for ${aircraft.asking_price:.1f}M cash?"
        elif financing_type == FinancingType.LEASE:
            message = f"Lease {aircraft.spec.model} for ${aircraft.lease_rate_monthly:.0f}k/month?"
        else:
            loan_amount = aircraft.asking_price - down_payment
            message = f"Finance {aircraft.spec.model}?\nDown payment: ${down_payment:.1f}M\nLoan amount: ${loan_amount:.1f}M"
        
        # Use ttkbootstrap's Messagebox.show_question
        result = Messagebox.show_question("Confirm Purchase", message)
        if not result == "Yes":
            return
        
        # Execute purchase
        try:
            success, message_text, owned_aircraft = self.marketplace.purchase_aircraft(
                aircraft.id, financing_type, down_payment
            )
            
            if success:
                Messagebox.show_info("Purchase Successful", 
                                  f"Successfully purchased {owned_aircraft.spec.model}!\n"
                                  f"Monthly payment: ${owned_aircraft.monthly_payment:.0f}k")
                self.load_market_aircraft()  # Refresh market
                self.refresh_fleet_data()    # Refresh fleet
            else:
                Messagebox.show_error("Purchase Failed", message_text)
        
        except Exception as e:
            Messagebox.show_error("Error", f"Purchase failed: {str(e)}")
    
    def refresh_fleet_data(self):
        """Refresh owned fleet data"""
        # Clear fleet treeview
        for item in self.fleet_tree.get_children():
            self.fleet_tree.delete(item)
        
        # Load owned aircraft
        try:
            owned_aircraft = self.marketplace.get_owned_aircraft()
            
            for aircraft in owned_aircraft:
                values = (
                    aircraft.spec.model,
                    f"{aircraft.age_years:.1f}",
                    f"{aircraft.current_value:.1f}",
                    f"{aircraft.monthly_payment:.0f}k",
                    aircraft.condition.value.title(),
                    aircraft.location,
                    f"{aircraft.total_flight_hours:,}",
                    len(aircraft.route_assignments)
                )
                
                item_id = self.fleet_tree.insert("", 'end', values=values)
                self.fleet_tree.set(item_id, "aircraft_obj", aircraft)
            
            # Update fleet statistics
            self.update_fleet_statistics(owned_aircraft)
        
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to load fleet data: {str(e)}")
    
    def update_fleet_statistics(self, owned_aircraft: List[OwnedAircraft]):
        """Update fleet statistics display"""
        self.fleet_stats_text.delete(1.0, 'end')
        
        if not owned_aircraft:
            self.fleet_stats_text.insert(1.0, "No aircraft in fleet.\n\n💡 Visit the Aircraft Market to purchase your first aircraft!")
            return
        
        # Calculate statistics
        total_aircraft = len(owned_aircraft)
        total_value = sum(aircraft.current_value for aircraft in owned_aircraft)
        monthly_costs = self.marketplace.calculate_monthly_costs()
        
        # Category breakdown
        category_counts = {}
        for aircraft in owned_aircraft:
            cat = aircraft.spec.category.value.replace('_', ' ').title()
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Average age and condition
        avg_age = sum(aircraft.age_years for aircraft in owned_aircraft) / total_aircraft
        
        # Total capacity
        total_pax_capacity = sum(aircraft.spec.passenger_capacity for aircraft in owned_aircraft)
        total_cargo_capacity = sum(aircraft.spec.cargo_capacity for aircraft in owned_aircraft)
        
        stats = f"""📊 FLEET SUMMARY

✈️ Total Aircraft: {total_aircraft}
💰 Fleet Value: ${total_value:.1f}M
📅 Average Age: {avg_age:.1f} years

💸 MONTHLY COSTS
🏦 Financing Payments: ${monthly_costs['financing_payments']:.0f}k
🔧 Maintenance Costs: ${monthly_costs['maintenance_costs']:.0f}k
📋 Total Monthly: ${monthly_costs['total_monthly']:.0f}k

🚀 CAPACITY
👥 Total Passengers: {total_pax_capacity:,}
📦 Total Cargo: {total_cargo_capacity:.1f} tons

🛩️ FLEET COMPOSITION
"""
        
        for category, count in category_counts.items():
            stats += f"• {category}: {count}\n"
        
        # Add ROI information
        if monthly_costs['total_monthly'] > 0:
            stats += f"""
📈 FINANCIAL METRICS
• Break-even needed: ${monthly_costs['total_monthly']*12:.0f}k/year
• Revenue per passenger needed: ${(monthly_costs['total_monthly']*12*1000)/max(total_pax_capacity, 1):.0f}/year
"""
        
        self.fleet_stats_text.insert(1.0, stats)
    
    def assign_route(self):
        """Assign route to selected aircraft"""
        Messagebox.show_info("Feature Coming Soon", "🗺️ Route assignment will be available in Phase 2!\n\nThis will include:\n• Route profitability analysis\n• Aircraft-route optimization\n• Dynamic pricing based on demand")
    
    def schedule_maintenance(self):
        """Schedule maintenance for selected aircraft"""
        Messagebox.show_info("Feature Coming Soon", "🔧 Maintenance scheduling will be available in Phase 2!\n\nThis will include:\n• Predictive maintenance\n• Cost optimization\n• Downtime minimization")
    
    def sell_aircraft(self):
        """Sell selected aircraft"""
        Messagebox.show_info("Feature Coming Soon", "💸 Aircraft selling will be available in Phase 2!\n\nThis will include:\n• Market value assessment\n• Depreciation calculations\n• Secondary market dynamics")


# Integration function for easy setup
def integrate_marketplace_gui(parent_notebook: ttk.Notebook, db_path: str):
    """Function to integrate marketplace GUI with existing application"""
    try:
        marketplace_gui = AircraftMarketplaceGUI(parent_notebook, db_path)
        return marketplace_gui
    except Exception as e:
        Messagebox.show_error("Marketplace Error", f"Failed to initialize aircraft marketplace: {str(e)}")
        return None