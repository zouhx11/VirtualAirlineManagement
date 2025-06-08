import flet as ft
import sqlite3
from datetime import datetime, timedelta
from core.config_manager import ConfigManager
from core.database_utils import fetch_pilot_data_new


class PilotDashboardView:
    def __init__(self, page: ft.Page, airline_id: int, airline_name: str):
        self.page = page
        self.airline_id = airline_id
        self.airline_name = airline_name
        self.config_manager = ConfigManager()
        
    def build(self):
        """Build the dashboard interface."""
        # Get statistics
        stats = self.get_statistics()
        
        return ft.Column(
            [
                ft.Text(
                    f"Dashboard - {self.airline_name}",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"Welcome to Virtual Airline Management",
                    size=16,
                    color="#616161",
                ),
                ft.Divider(),
                
                # Key Statistics Cards
                ft.Row(
                    [
                        self.create_stat_card(
                            "Total Pilots", 
                            str(stats['total_pilots']),
                            ft.Icons.PERSON,
                            "#2196f3",
                        ),
                        self.create_stat_card(
                            "Active Pilots", 
                            str(stats['active_pilots']),
                            ft.Icons.FLIGHT_TAKEOFF,
                            "#4caf50",
                        ),
                        self.create_stat_card(
                            "Total Hours", 
                            f"{stats['total_hours']:,}",
                            ft.Icons.ACCESS_TIME,
                            "#ff9800",
                        ),
                        self.create_stat_card(
                            "Aircraft", 
                            str(stats['total_aircraft']),
                            ft.Icons.AIRPLANEMODE_ACTIVE,
                            "#9c27b0",
                        ),
                    ],
                    wrap=True,
                ),
                
                ft.Container(height=20),
                
                # Quick Actions
                ft.Container(
                    content=ft.Column([
                        ft.Text("Quick Actions", size=20, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Row([
                            ft.ElevatedButton(
                                "Add New Pilot",
                                icon=ft.Icons.PERSON_ADD,
                                on_click=self.add_pilot_action,
                                style=ft.ButtonStyle(bgcolor="#4caf50"),
                            ),
                            ft.ElevatedButton(
                                "View Fleet",
                                icon=ft.Icons.AIRPLANEMODE_ACTIVE,
                                on_click=self.view_fleet_action,
                                style=ft.ButtonStyle(bgcolor="#2196f3"),
                            ),
                            ft.ElevatedButton(
                                "Schedule Flight",
                                icon=ft.Icons.SCHEDULE,
                                on_click=self.schedule_flight_action,
                                style=ft.ButtonStyle(bgcolor="#9c27b0"),
                            ),
                            ft.ElevatedButton(
                                "Aircraft Market",
                                icon=ft.Icons.SHOPPING_CART,
                                on_click=self.aircraft_market_action,
                                style=ft.ButtonStyle(bgcolor="#ff9800"),
                            ),
                        ], wrap=True),
                    ]),
                    padding=20,
                    border=ft.border.all(1, "#e0e0e0"),
                    border_radius=10,
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def create_stat_card(self, title: str, value: str, icon, color):
        """Create a statistics card."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=30),
                    ft.Column([
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(title, size=12, color="#757575"),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            border=ft.border.all(1, "#e0e0e0"),
            border_radius=10,
            bgcolor="#ffffff",
            width=200,
            height=100,
        )

    def get_statistics(self):
        """Get airline statistics."""
        stats = {
            'total_pilots': 0,
            'active_pilots': 0,
            'total_hours': 0,
            'total_aircraft': 0,
        }
        
        try:
            # Get pilot statistics
            pilots = fetch_pilot_data_new(self.airline_id)
            stats['total_pilots'] = len(pilots)
            stats['active_pilots'] = len([p for p in pilots if p.get('status') == 'active'])
            stats['total_hours'] = sum(p.get('hours', 0) for p in pilots)
            
            # Get aircraft statistics
            user_db = self.config_manager.get_database_path('userdata')
            with sqlite3.connect(user_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM aircraft WHERE airline_id = ?", (self.airline_id,))
                result = cursor.fetchone()
                stats['total_aircraft'] = result[0] if result else 0
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
        
        return stats

    def add_pilot_action(self, e):
        """Handle add pilot quick action."""
        self.show_info("Quick Action", "Navigate to Pilot Management to add a new pilot.")

    def view_fleet_action(self, e):
        """Handle view fleet quick action."""
        self.show_info("Quick Action", "Navigate to Fleet Management to view your aircraft.")

    def schedule_flight_action(self, e):
        """Handle schedule flight quick action."""
        self.show_info("Quick Action", "Navigate to Schedules to plan your flights.")

    def aircraft_market_action(self, e):
        """Handle aircraft market quick action."""
        self.show_info("Quick Action", "Navigate to Aircraft Marketplace to buy or lease aircraft.")

    def show_info(self, title: str, message: str):
        """Show info dialog."""
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()