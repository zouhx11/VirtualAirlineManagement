# modules/route_economics_view.py

import flet as ft
from typing import List, Dict, Optional
import json

from core.config_manager import ConfigManager
from modules.route_management import RouteEconomics, RouteData, RouteAssignment
from modules.aircraft_marketplace import AircraftMarketplace

class RouteEconomicsView:
    """Flet-based Route Economics management interface"""
    
    def __init__(self, page: ft.Page, airline_id: int):
        self.page = page
        self.airline_id = airline_id
        
        # Initialize systems
        self.config_manager = ConfigManager()
        db_path = self.config_manager.get_database_path('userdata')
        self.route_system = RouteEconomics(db_path)
        self.aircraft_marketplace = AircraftMarketplace(db_path)
        
        # Data storage
        self.all_routes = []
        self.owned_aircraft = []
        self.route_assignments = []
        
        # UI components
        self.routes_data_table = None
        self.analysis_text = None
        self.assignments_data_table = None
        self.performance_data_table = None
        
        # Summary cards
        self.total_routes_card = None
        self.active_aircraft_card = None
        self.monthly_revenue_card = None
        self.monthly_profit_card = None
        
    def build_view(self) -> ft.Control:
        """Build the main route economics view"""
        self.load_initial_data()
        
        # Create tabs
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Route Network",
                    icon=ft.icons.MAP,
                    content=self.build_route_network_tab()
                ),
                ft.Tab(
                    text="Route Analysis", 
                    icon=ft.icons.ANALYTICS,
                    content=self.build_route_analysis_tab()
                ),
                ft.Tab(
                    text="Aircraft Assignment",
                    icon=ft.icons.AIRPLANEMODE_ACTIVE,
                    content=self.build_aircraft_assignment_tab()
                ),
                ft.Tab(
                    text="Performance Dashboard",
                    icon=ft.icons.DASHBOARD,
                    content=self.build_performance_tab()
                )
            ],
            expand=True
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Route Economics", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                tabs
            ]),
            padding=20,
            expand=True
        )
    
    def build_route_network_tab(self) -> ft.Control:
        """Build the route network management tab"""
        
        # Control buttons
        controls_row = ft.Row([
            ft.ElevatedButton(
                "Generate Routes",
                icon=ft.icons.ADD_LOCATION,
                on_click=self.generate_routes
            ),
            ft.ElevatedButton(
                "Refresh",
                icon=ft.icons.REFRESH,
                on_click=self.refresh_routes
            ),
            ft.Container(expand=True),  # Spacer
            ft.TextField(
                label="Search routes...",
                width=200,
                on_change=self.filter_routes
            )
        ])
        
        # Routes data table
        self.routes_data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Origin")),
                ft.DataColumn(ft.Text("Destination")),
                ft.DataColumn(ft.Text("Distance (nm)")),
                ft.DataColumn(ft.Text("Type")),
                ft.DataColumn(ft.Text("Demand")),
                ft.DataColumn(ft.Text("Competition")),
                ft.DataColumn(ft.Text("Market Fare")),
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
        )
        
        return ft.Container(
            content=ft.Column([
                controls_row,
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        self.routes_data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    height=500,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    padding=10
                )
            ]),
            padding=20
        )
    
    def build_route_analysis_tab(self) -> ft.Control:
        """Build the route analysis tab"""
        
        # Left panel - Controls
        route_dropdown = ft.Dropdown(
            label="Select Route",
            width=300,
            on_change=self.on_route_selected_for_analysis
        )
        
        aircraft_dropdown = ft.Dropdown(
            label="Select Aircraft",
            width=300,
            on_change=self.on_aircraft_selected_for_analysis
        )
        
        frequency_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="7", label="Daily (7x/week)"),
                ft.Radio(value="14", label="Twice Daily (14x/week)"),
                ft.Radio(value="21", label="Three Times Daily (21x/week)"),
            ]),
            value="7"
        )
        
        economy_fare_field = ft.TextField(
            label="Economy Fare ($)",
            value="200",
            width=200
        )
        
        business_fare_field = ft.TextField(
            label="Business Fare ($)",
            value="600",
            width=200
        )
        
        analyze_button = ft.ElevatedButton(
            "Analyze Route",
            icon=ft.icons.ANALYTICS,
            on_click=lambda e: self.analyze_route(
                route_dropdown.value,
                aircraft_dropdown.value,
                frequency_radio.value,
                economy_fare_field.value,
                business_fare_field.value
            )
        )
        
        left_panel = ft.Container(
            content=ft.Column([
                ft.Text("Route Analysis", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                route_dropdown,
                aircraft_dropdown,
                ft.Text("Weekly Frequency:", weight=ft.FontWeight.BOLD),
                frequency_radio,
                ft.Text("Pricing:", weight=ft.FontWeight.BOLD),
                economy_fare_field,
                business_fare_field,
                analyze_button
            ]),
            width=350,
            padding=20
        )
        
        # Right panel - Results
        self.analysis_text = ft.Container(
            content=ft.Text(
                "Select a route and aircraft to analyze profitability...",
                size=12
            ),
            padding=20,
            bgcolor=ft.colors.GREY_100,
            border_radius=8,
            expand=True
        )
        
        # Store references for later updates
        self.route_dropdown = route_dropdown
        self.aircraft_dropdown = aircraft_dropdown
        self.frequency_radio = frequency_radio
        self.economy_fare_field = economy_fare_field
        self.business_fare_field = business_fare_field
        
        return ft.Row([
            left_panel,
            ft.VerticalDivider(),
            ft.Container(
                content=ft.Column([
                    ft.Text("Analysis Results", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.analysis_text
                ]),
                expand=True,
                padding=20
            )
        ])
    
    def build_aircraft_assignment_tab(self) -> ft.Control:
        """Build the aircraft assignment tab"""
        
        # Control buttons
        controls_row = ft.Row([
            ft.ElevatedButton(
                "Optimize Assignments",
                icon=ft.icons.AUTO_FIX_HIGH,
                on_click=self.optimize_assignments
            ),
            ft.ElevatedButton(
                "Assign Selected",
                icon=ft.icons.ASSIGNMENT_ADD,
                on_click=self.assign_aircraft_to_route
            ),
            ft.ElevatedButton(
                "Refresh",
                icon=ft.icons.REFRESH,
                on_click=self.refresh_assignments
            )
        ])
        
        # Assignments data table
        self.assignments_data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Aircraft")),
                ft.DataColumn(ft.Text("Route")),
                ft.DataColumn(ft.Text("Frequency")),
                ft.DataColumn(ft.Text("Economy Fare")),
                ft.DataColumn(ft.Text("Business Fare")),
                ft.DataColumn(ft.Text("Monthly Profit")),
                ft.DataColumn(ft.Text("Load Factor")),
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
        )
        
        return ft.Container(
            content=ft.Column([
                controls_row,
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        self.assignments_data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    height=500,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    padding=10
                )
            ]),
            padding=20
        )
    
    def build_performance_tab(self) -> ft.Control:
        """Build the performance dashboard tab"""
        
        # Summary cards
        self.total_routes_card = self.create_summary_card("Total Routes", "0", ft.icons.MAP)
        self.active_aircraft_card = self.create_summary_card("Active Aircraft", "0", ft.icons.AIRPLANEMODE_ACTIVE)
        self.monthly_revenue_card = self.create_summary_card("Monthly Revenue", "$0", ft.icons.MONETIZATION_ON)
        self.monthly_profit_card = self.create_summary_card("Monthly Profit", "$0", ft.icons.TRENDING_UP)
        
        summary_row = ft.Row([
            self.total_routes_card,
            self.active_aircraft_card,
            self.monthly_revenue_card,
            self.monthly_profit_card
        ], spacing=20)
        
        # Performance data table
        self.performance_data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Route")),
                ft.DataColumn(ft.Text("Flights")),
                ft.DataColumn(ft.Text("Passengers")),
                ft.DataColumn(ft.Text("Revenue")),
                ft.DataColumn(ft.Text("Costs")),
                ft.DataColumn(ft.Text("Profit")),
                ft.DataColumn(ft.Text("Load Factor")),
                ft.DataColumn(ft.Text("On-Time %")),
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
        )
        
        return ft.Container(
            content=ft.Column([
                summary_row,
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Route Performance", size=18, weight=ft.FontWeight.BOLD),
                        self.performance_data_table
                    ], scroll=ft.ScrollMode.AUTO),
                    height=400,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    padding=10
                )
            ]),
            padding=20
        )
    
    def create_summary_card(self, title: str, value: str, icon: str) -> ft.Container:
        """Create a summary metric card"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=24, color=ft.colors.BLUE),
                    ft.Text(title, size=12, color=ft.colors.GREY_600)
                ]),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD)
            ]),
            padding=20,
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.colors.GREY_300),
            expand=True
        )
    
    def load_initial_data(self):
        """Load initial data for the interface"""
        try:
            # Get airline hub
            airline_data = self.get_airline_data()
            hub = airline_data.get('hub', 'KJFK') if airline_data else 'KJFK'
            
            # Load routes
            self.all_routes = self.route_system.get_routes(hub)
            
            # Load aircraft
            self.owned_aircraft = self.aircraft_marketplace.get_owned_aircraft()
            
            # Load assignments
            self.route_assignments = self.route_system.get_route_assignments()
            
            # Update UI
            self.update_routes_table()
            self.update_dropdowns()
            self.update_assignments_table()
            self.update_summary_cards()
            
        except Exception as e:
            self.show_error(f"Error loading data: {str(e)}")
    
    def update_routes_table(self):
        """Update the routes data table"""
        if not self.routes_data_table:
            return
        
        self.routes_data_table.rows.clear()
        
        for route in self.all_routes:
            self.routes_data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(route.origin_icao)),
                        ft.DataCell(ft.Text(route.destination_icao)),
                        ft.DataCell(ft.Text(f"{route.distance_nm:,}")),
                        ft.DataCell(ft.Text(route.route_type.value.title())),
                        ft.DataCell(ft.Text(route.base_demand.value.replace('_', ' ').title())),
                        ft.DataCell(ft.Text(f"{route.competition_level}/10")),
                        ft.DataCell(ft.Text(f"${route.market_fare_economy:.0f}")),
                    ]
                )
            )
        
        self.page.update()
    
    def update_dropdowns(self):
        """Update dropdown options"""
        if hasattr(self, 'route_dropdown'):
            route_options = [
                ft.dropdown.Option(key=route.id, text=f"{route.origin_icao} → {route.destination_icao}")
                for route in self.all_routes
            ]
            self.route_dropdown.options = route_options
        
        if hasattr(self, 'aircraft_dropdown'):
            aircraft_options = [
                ft.dropdown.Option(key=aircraft.id, text=f"{aircraft.spec.model} ({aircraft.id})")
                for aircraft in self.owned_aircraft
            ]
            self.aircraft_dropdown.options = aircraft_options
        
        self.page.update()
    
    def update_assignments_table(self):
        """Update the assignments data table"""
        if not self.assignments_data_table:
            return
        
        self.assignments_data_table.rows.clear()
        
        for assignment in self.route_assignments:
            # Get route info
            route = next((r for r in self.all_routes if r.id == assignment.route_id), None)
            route_name = f"{route.origin_icao} → {route.destination_icao}" if route else assignment.route_id
            
            # Get aircraft info
            aircraft = next((a for a in self.owned_aircraft if a.id == assignment.aircraft_id), None)
            aircraft_name = aircraft.spec.model if aircraft else assignment.aircraft_id
            
            self.assignments_data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(aircraft_name)),
                        ft.DataCell(ft.Text(route_name)),
                        ft.DataCell(ft.Text(f"{assignment.frequency_weekly}x/week")),
                        ft.DataCell(ft.Text(f"${assignment.fare_economy:.0f}")),
                        ft.DataCell(ft.Text(f"${assignment.fare_business:.0f}")),
                        ft.DataCell(ft.Text("Calculating...")),
                        ft.DataCell(ft.Text(f"{assignment.load_factor_target:.1%}")),
                    ]
                )
            )
        
        self.page.update()
    
    def update_summary_cards(self):
        """Update summary metric cards"""
        if not all([self.total_routes_card, self.active_aircraft_card, 
                   self.monthly_revenue_card, self.monthly_profit_card]):
            return
        
        # Update values
        self.total_routes_card.content.controls[1].value = str(len(self.all_routes))
        
        unique_aircraft = len(set(assignment.aircraft_id for assignment in self.route_assignments))
        self.active_aircraft_card.content.controls[1].value = str(unique_aircraft)
        
        # For now, use placeholder values - in a real implementation, these would be calculated
        self.monthly_revenue_card.content.controls[1].value = "$0"
        self.monthly_profit_card.content.controls[1].value = "$0"
        
        self.page.update()
    
    def generate_routes(self, e):
        """Generate new routes for the airline"""
        try:
            airline_data = self.get_airline_data()
            hub = airline_data.get('hub', 'KJFK') if airline_data else 'KJFK'
            
            # Generate routes
            routes = self.route_system.generate_routes(hub, 25)
            self.route_system.save_routes(routes)
            
            self.show_success(f"Generated {len(routes)} routes from {hub}")
            self.refresh_routes(e)
            
        except Exception as ex:
            self.show_error(f"Error generating routes: {str(ex)}")
    
    def refresh_routes(self, e):
        """Refresh routes data"""
        self.load_initial_data()
    
    def filter_routes(self, e):
        """Filter routes based on search"""
        # Implement route filtering logic here
        pass
    
    def on_route_selected_for_analysis(self, e):
        """Handle route selection for analysis"""
        # Update fare fields with market rates
        if e.control.value:
            route = next((r for r in self.all_routes if r.id == e.control.value), None)
            if route:
                self.economy_fare_field.value = str(int(route.market_fare_economy * 0.9))
                self.business_fare_field.value = str(int(route.market_fare_business * 0.9))
                self.page.update()
    
    def on_aircraft_selected_for_analysis(self, e):
        """Handle aircraft selection for analysis"""
        pass
    
    def analyze_route(self, route_id: str, aircraft_id: str, frequency: str, 
                     economy_fare: str, business_fare: str):
        """Analyze route profitability"""
        if not all([route_id, aircraft_id, frequency, economy_fare, business_fare]):
            self.show_error("Please fill in all fields")
            return
        
        try:
            route = next((r for r in self.all_routes if r.id == route_id), None)
            aircraft = next((a for a in self.owned_aircraft if a.id == aircraft_id), None)
            
            if not route or not aircraft:
                self.show_error("Invalid route or aircraft selection")
                return
            
            aircraft_spec = {
                'passenger_capacity': aircraft.spec.passenger_capacity,
                'cruise_speed': aircraft.spec.cruise_speed,
                'fuel_burn_per_hour': aircraft.spec.fuel_burn_per_hour,
                'crew_required': aircraft.spec.crew_required,
                'base_price': aircraft.spec.base_price
            }
            
            analysis = self.route_system.calculate_route_profitability(
                route_id, aircraft_spec, int(frequency), float(economy_fare), float(business_fare)
            )
            
            if "error" in analysis:
                self.show_error(f"Analysis error: {analysis['error']}")
                return
            
            # Display results
            self.display_analysis_results(route, aircraft, frequency, economy_fare, business_fare, analysis)
            
        except Exception as ex:
            self.show_error(f"Error analyzing route: {str(ex)}")
    
    def display_analysis_results(self, route, aircraft, frequency, economy_fare, business_fare, analysis):
        """Display route analysis results"""
        results_text = f"""
ROUTE ANALYSIS RESULTS
{'='*50}

Route: {route.origin_icao} → {route.destination_icao}
Aircraft: {aircraft.spec.model}
Frequency: {frequency}x per week
Distance: {route.distance_nm:,} nautical miles

PRICING
Economy Fare: ${float(economy_fare):.2f}
Business Fare: ${float(business_fare):.2f}
Market Fare: ${route.market_fare_economy:.2f} (Economy)

REVENUE ANALYSIS
Expected Load Factor: {analysis['revenue']['load_factor']:.1%}
Passengers per Flight: {analysis['revenue']['passengers_per_flight']:.0f}
Flights per Month: {analysis['revenue']['flights_per_month']:.0f}
Monthly Passengers: {analysis['revenue']['monthly_passengers']:.0f}
Monthly Revenue: ${analysis['revenue']['monthly_revenue']:,.2f}

COST ANALYSIS
Monthly Fuel: ${analysis['costs']['breakdown']['fuel']:,.2f}
Monthly Crew: ${analysis['costs']['breakdown']['crew']:,.2f}
Monthly Airport Fees: ${analysis['costs']['breakdown']['airport_fees']:,.2f}
Monthly Maintenance: ${analysis['costs']['breakdown']['maintenance']:,.2f}
Total Monthly Costs: ${analysis['costs']['monthly_total']:,.2f}

PROFITABILITY
Monthly Profit: ${analysis['profitability']['monthly_profit']:,.2f}
Profit Margin: {analysis['profitability']['profit_margin']:.1f}%
Break-even Load Factor: {analysis['profitability']['breakeven_load_factor']:.1%}

RECOMMENDATION
"""
        
        if analysis['profitability']['monthly_profit'] > 0:
            results_text += f"✅ PROFITABLE ROUTE\n"
            results_text += f"Expected monthly profit: ${analysis['profitability']['monthly_profit']:,.2f}\n"
            if analysis['profitability']['profit_margin'] > 20:
                results_text += "🌟 Excellent profit margin!"
            elif analysis['profitability']['profit_margin'] > 10:
                results_text += "👍 Good profit margin"
            else:
                results_text += "⚠️ Low profit margin - consider adjusting pricing"
        else:
            results_text += f"❌ UNPROFITABLE ROUTE\n"
            results_text += f"Expected monthly loss: ${abs(analysis['profitability']['monthly_profit']):,.2f}\n"
            results_text += "💡 Consider reducing frequency or adjusting pricing"
        
        self.analysis_text.content = ft.Text(
            results_text,
            size=10,
            font_family="Courier New"
        )
        self.page.update()
    
    def optimize_assignments(self, e):
        """Optimize aircraft assignments"""
        try:
            # Get available aircraft
            current_assignments = self.route_system.get_route_assignments()
            assigned_aircraft_ids = {assignment.aircraft_id for assignment in current_assignments}
            
            available_aircraft = [
                {
                    'id': aircraft.id,
                    'spec': {
                        'passenger_capacity': aircraft.spec.passenger_capacity,
                        'cruise_speed': aircraft.spec.cruise_speed,
                        'fuel_burn_per_hour': aircraft.spec.fuel_burn_per_hour,
                        'crew_required': aircraft.spec.crew_required,
                        'base_price': aircraft.spec.base_price
                    }
                }
                for aircraft in self.owned_aircraft
                if aircraft.id not in assigned_aircraft_ids
            ]
            
            if not available_aircraft:
                self.show_info("No available aircraft for assignment")
                return
            
            # Get available routes
            available_route_ids = [route.id for route in self.all_routes]
            
            # Optimize
            optimization_results = self.route_system.optimize_aircraft_assignment(
                available_aircraft, available_route_ids
            )
            
            # Update assignments table with recommendations
            self.assignments_data_table.rows.clear()
            
            for result in optimization_results[:10]:  # Show top 10 recommendations
                aircraft = next(a for a in self.owned_aircraft if a.id == result['aircraft_id'])
                route = next(r for r in self.all_routes if r.id == result['recommended_route'])
                
                config = result['configuration']
                
                self.assignments_data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{aircraft.spec.model} ({result['aircraft_id']})")),
                            ft.DataCell(ft.Text(f"{route.origin_icao} → {route.destination_icao}")),
                            ft.DataCell(ft.Text(f"{config['frequency_weekly']}x/week")),
                            ft.DataCell(ft.Text(f"${config['fare_economy']:.0f}")),
                            ft.DataCell(ft.Text(f"${config['fare_business']:.0f}")),
                            ft.DataCell(ft.Text(f"${result['monthly_profit']:,.0f}")),
                            ft.DataCell(ft.Text(f"{config['profitability']['revenue']['load_factor']:.1%}")),
                        ]
                    )
                )
            
            self.show_success(f"Found {len(optimization_results)} optimization recommendations")
            self.page.update()
            
        except Exception as ex:
            self.show_error(f"Error optimizing assignments: {str(ex)}")
    
    def assign_aircraft_to_route(self, e):
        """Assign selected aircraft to route"""
        self.show_info("Aircraft assignment feature coming soon!")
    
    def refresh_assignments(self, e):
        """Refresh assignments data"""
        self.load_initial_data()
    
    def get_airline_data(self):
        """Get airline data from config"""
        try:
            with open('airline_data.json', 'r') as f:
                airlines = json.load(f)
            
            # Find airline by ID
            for airline in airlines:
                if airline['id'] == self.airline_id:
                    return airline
            
            return None
        except Exception:
            return None
    
    def show_error(self, message: str):
        """Show error snackbar"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.colors.RED_400
            )
        )
    
    def show_success(self, message: str):
        """Show success snackbar"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.colors.GREEN_400
            )
        )
    
    def show_info(self, message: str):
        """Show info snackbar"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.colors.BLUE_400
            )
        )