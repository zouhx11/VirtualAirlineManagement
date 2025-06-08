import flet as ft
import sqlite3
import os
from typing import Optional

from core.config_manager import ConfigManager
from core.database_utils import fetch_pilot_data_new, add_pilot
from core.utils import load_airlines_json
from modules.pilot_management import PilotManagementView
from modules.aircraft_marketplace_view import AircraftMarketplaceView
from modules.fleet_management_view import FleetManagementView
from modules.pilot_logbook_view import PilotLogbookView
from modules.pilot_dashboard_view import PilotDashboardView
from modules.schedule_view import ScheduleView
from modules.settings_view import SettingsView
from modules.route_economics_view import RouteEconomicsView


class VirtualAirlineApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.config_manager = ConfigManager()
        self.selected_airline_id = None
        self.selected_airline_name = ""
        self.current_view = None
        
        # Configure page
        self.setup_page()
        
        # Load user preferences
        self.load_preferences()
        
        # Ensure database structure
        self.ensure_database_structure()
        
        # Build main layout
        self.build_main_layout()
        
    def setup_page(self):
        """Configure the main page settings."""
        self.page.title = "Virtual Airline Management"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 800
        self.page.window_min_height = 600
        self.page.padding = 20
        self.page.bgcolor = "#eceff1"  # Blue grey 50

    def load_preferences(self):
        """Load saved preferences from config."""
        saved_airline = self.config_manager.get_preference('selected_airline', '')
        if saved_airline and "(ID: " in saved_airline:
            try:
                self.selected_airline_id = int(saved_airline.split("(ID: ")[1].split(")")[0])
                self.selected_airline_name = saved_airline.split(" (ID: ")[0]
            except (IndexError, ValueError):
                self.selected_airline_id = None
                self.selected_airline_name = ""

    def ensure_database_structure(self):
        """Ensure database has correct structure."""
        try:
            user_db = self.config_manager.get_database_path('userdata')
            
            if not os.path.exists(user_db):
                self.show_error("Database Missing", 
                              "Database file not found. Please run scripts/initial_setup.py")
                return
                
            with sqlite3.connect(user_db) as conn:
                cursor = conn.cursor()
                
                # Check if pilots table exists and has airline_id column
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pilots'")
                if not cursor.fetchone():
                    self.show_error("Database Error", 
                                  "Pilots table missing. Please run scripts/initial_setup.py")
                    return
                
                cursor.execute("PRAGMA table_info(pilots)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'airline_id' not in columns:
                    cursor.execute("ALTER TABLE pilots ADD COLUMN airline_id INTEGER DEFAULT 1")
                    conn.commit()
                    
        except Exception as e:
            self.show_error("Database Error", f"Failed to initialize database: {str(e)}")

    def show_error(self, title: str, message: str):
        """Show error dialog."""
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_success(self, title: str, message: str):
        """Show success dialog."""
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def build_main_layout(self):
        """Build the main application layout."""
        # App bar
        self.page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.FLIGHT),
            leading_width=40,
            title=ft.Text("Virtual Airline Management"),
            center_title=False,
            bgcolor="#e7e0ec",  # Surface variant
            actions=[
                ft.IconButton(ft.Icons.SETTINGS, on_click=self.open_settings),
                ft.IconButton(ft.Icons.REFRESH, on_click=self.refresh_data),
            ],
        )

        # Navigation rail
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD,
                    label="Dashboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PERSON_OUTLINE,
                    selected_icon=ft.Icons.PERSON,
                    label="Pilots",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.FLIGHT_OUTLINED,
                    selected_icon=ft.Icons.FLIGHT,
                    label="Fleet",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SHOPPING_CART_OUTLINED,
                    selected_icon=ft.Icons.SHOPPING_CART,
                    label="Marketplace",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SCHEDULE_OUTLINED,
                    selected_icon=ft.Icons.SCHEDULE,
                    label="Schedules",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.BOOK_OUTLINED,
                    selected_icon=ft.Icons.BOOK,
                    label="Logbook",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.MAP_OUTLINED,
                    selected_icon=ft.Icons.MAP,
                    label="Routes",
                ),
            ],
            on_change=self.nav_changed,
        )

        # Main content area
        self.content_area = ft.Container(
            expand=True,
            padding=20,
        )

        # Airline selection (shown if no airline selected)
        if not self.selected_airline_id:
            self.show_airline_selection()
        else:
            self.show_dashboard()

        # Main layout
        main_layout = ft.Row(
            [
                self.nav_rail,
                ft.VerticalDivider(width=1),
                self.content_area,
            ],
            expand=True,
        )

        self.page.add(main_layout)

    def show_airline_selection(self):
        """Show airline selection interface."""
        airlines = load_airlines_json()
        if not airlines:
            self.show_error("Airline Data Error", 
                          "No airline data available. Please run scripts/create_airline_data.py")
            return

        airline_options = [
            ft.dropdown.Option(f"{airline['id']}", f"{airline['name']} (ID: {airline['id']})")
            for airline in airlines
        ]

        self.airline_dropdown = ft.Dropdown(
            label="Select Airline",
            hint_text="Choose your airline",
            options=airline_options,
            value=str(self.selected_airline_id) if self.selected_airline_id else None,
            width=400,
        )

        def confirm_airline(e):
            if not self.airline_dropdown.value:
                self.show_error("Warning", "Please select an airline!")
                return
            
            try:
                airline_id = int(self.airline_dropdown.value)
                selected_option = next(opt for opt in airline_options if opt.key == str(airline_id))
                airline_name = selected_option.text.split(" (ID: ")[0]
                
                self.selected_airline_id = airline_id
                self.selected_airline_name = airline_name
                
                # Save preference
                self.config_manager.set_preference('selected_airline', f"{airline_name} (ID: {airline_id})")
                
                # Update pilots table
                self.update_pilot_airline(airline_id)
                
                self.show_success("Success", f"Airline '{airline_name}' selected successfully!")
                
                # Switch to dashboard
                self.show_dashboard()
                
            except Exception as ex:
                self.show_error("Error", f"Failed to select airline: {str(ex)}")

        airline_selection = ft.Column(
            [
                ft.Text("Welcome to Virtual Airline Management", 
                       size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Please select your airline to continue", size=16),
                ft.Container(height=30),
                self.airline_dropdown,
                ft.Container(height=20),
                ft.ElevatedButton(
                    text="Confirm Airline",
                    on_click=confirm_airline,
                    style=ft.ButtonStyle(
                        bgcolor="#2196f3",  # Blue
                        color="#ffffff",    # White
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content_area.content = ft.Container(
            content=airline_selection,
            alignment=ft.alignment.center,
        )
        self.page.update()

    def update_pilot_airline(self, airline_id: int):
        """Update pilot records with selected airline."""
        try:
            user_db = self.config_manager.get_database_path('userdata')
            with sqlite3.connect(user_db) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM pilots")
                pilot_count = cursor.fetchone()[0]
                
                if pilot_count == 0:
                    # Create default pilot
                    cursor.execute("""
                        INSERT INTO pilots (name, license_number, rating, hours, hire_date, status, airline_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "Default Pilot", "ATP001", "ATP", 1000, 
                        "2024-01-01", "active", airline_id
                    ))
                else:
                    # Update existing pilots
                    cursor.execute("UPDATE pilots SET airline_id = ?", (airline_id,))
                
                conn.commit()
                
        except Exception as e:
            self.show_error("Database Error", f"Failed to update pilot airline: {str(e)}")

    def nav_changed(self, e):
        """Handle navigation rail selection changes."""
        if not self.selected_airline_id:
            self.show_airline_selection()
            return
            
        selected_index = e.control.selected_index
        
        if selected_index == 0:
            self.show_dashboard()
        elif selected_index == 1:
            self.show_pilot_management()
        elif selected_index == 2:
            self.show_fleet_management()
        elif selected_index == 3:
            self.show_aircraft_marketplace()
        elif selected_index == 4:
            self.show_schedules()
        elif selected_index == 5:
            self.show_logbook()
        elif selected_index == 6:
            self.show_route_economics()

    def show_dashboard(self):
        """Show pilot dashboard."""
        if not self.selected_airline_id:
            self.show_airline_selection()
            return
            
        dashboard_view = PilotDashboardView(
            self.page, self.selected_airline_id, self.selected_airline_name
        )
        self.content_area.content = dashboard_view.build()
        self.page.update()

    def show_pilot_management(self):
        """Show pilot management interface."""
        pilot_view = PilotManagementView(
            self.page, self.selected_airline_id, self.selected_airline_name
        )
        self.content_area.content = pilot_view.build()
        self.page.update()

    def show_fleet_management(self):
        """Show fleet management interface."""
        fleet_view = FleetManagementView(
            self.page, self.selected_airline_id
        )
        self.content_area.content = fleet_view.build()
        self.page.update()

    def show_aircraft_marketplace(self):
        """Show aircraft marketplace."""
        marketplace_view = AircraftMarketplaceView(self.page)
        self.content_area.content = marketplace_view.build()
        self.page.update()

    def show_schedules(self):
        """Show flight schedules."""
        schedule_view = ScheduleView(
            self.page, self.selected_airline_id
        )
        self.content_area.content = schedule_view.build()
        self.page.update()

    def show_logbook(self):
        """Show pilot logbook."""
        logbook_view = PilotLogbookView(self.page)
        self.content_area.content = logbook_view.build()
        self.page.update()

    def show_route_economics(self):
        """Show route economics management."""
        if not self.selected_airline_id:
            self.show_airline_selection()
            return
            
        route_economics_view = RouteEconomicsView(self.page, self.selected_airline_id)
        self.content_area.content = route_economics_view.build_view()
        self.page.update()

    def open_settings(self, e):
        """Open settings dialog."""
        settings_view = SettingsView(self.page)
        settings_view.show_dialog()

    def refresh_data(self, e):
        """Refresh current view data."""
        # Trigger refresh of current view
        current_index = self.nav_rail.selected_index
        self.nav_changed(type('obj', (object,), {'control': type('obj', (object,), {'selected_index': current_index})})())


def main(page: ft.Page):
    """Main entry point for Flet app."""
    VirtualAirlineApp(page)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8000)