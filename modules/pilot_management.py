import flet as ft
import sqlite3
from datetime import datetime
from core.config_manager import ConfigManager
from core.database_utils import fetch_pilot_data_new, add_pilot, update_pilot, delete_pilot


class PilotManagementView:
    def __init__(self, page: ft.Page, airline_id: int, airline_name: str):
        self.page = page
        self.airline_id = airline_id
        self.airline_name = airline_name
        self.config_manager = ConfigManager()
        self.pilots = []
        self.selected_pilot = None
        
        # Form fields
        self.pilot_name = ft.TextField(label="Pilot Name", width=300)
        self.license_number = ft.TextField(label="License Number", width=300)
        self.rating = ft.Dropdown(
            label="Rating",
            width=300,
            options=[
                ft.dropdown.Option("PPL", "Private Pilot License"),
                ft.dropdown.Option("CPL", "Commercial Pilot License"),
                ft.dropdown.Option("ATPL", "Airline Transport Pilot License"),
                ft.dropdown.Option("ATP", "Airline Transport Pilot"),
            ],
        )
        self.hours = ft.TextField(label="Flight Hours", width=300, keyboard_type=ft.KeyboardType.NUMBER)
        self.status = ft.Dropdown(
            label="Status",
            width=300,
            options=[
                ft.dropdown.Option("active", "Active"),
                ft.dropdown.Option("inactive", "Inactive"),
                ft.dropdown.Option("training", "In Training"),
                ft.dropdown.Option("leave", "On Leave"),
            ],
        )
        self.home_hub = ft.TextField(label="Home Hub (ICAO)", width=300)
        self.current_location = ft.TextField(label="Current Location (ICAO)", width=300)
        
        # Data table
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("License")),
                ft.DataColumn(ft.Text("Rating")),
                ft.DataColumn(ft.Text("Hours")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Hub")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
        )
        
        self.load_pilots()

    def build(self):
        """Build the pilot management interface."""
        return ft.Column(
            [
                ft.Text(
                    f"Pilot Management - {self.airline_name}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                
                # Form section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Add/Edit Pilot", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Column([
                                self.pilot_name,
                                self.license_number,
                                self.rating,
                            ]),
                            ft.Column([
                                self.hours,
                                self.status,
                                self.home_hub,
                            ]),
                            ft.Column([
                                self.current_location,
                                ft.Container(height=20),
                                ft.Row([
                                    ft.ElevatedButton(
                                        "Add Pilot",
                                        icon=ft.Icons.ADD,
                                        on_click=self.add_pilot_clicked,
                                        style=ft.ButtonStyle(bgcolor="#4caf50"),
                                    ),
                                    ft.ElevatedButton(
                                        "Update Pilot",
                                        icon=ft.Icons.UPDATE,
                                        on_click=self.update_pilot_clicked,
                                        style=ft.ButtonStyle(bgcolor="#2196f3"),
                                    ),
                                    ft.ElevatedButton(
                                        "Clear Form",
                                        icon=ft.Icons.CLEAR,
                                        on_click=self.clear_form,
                                        style=ft.ButtonStyle(bgcolor="#9e9e9e"),
                                    ),
                                ]),
                            ]),
                        ]),
                    ]),
                    padding=20,
                    border=ft.border.all(1, "#e0e0e0"),
                    border_radius=10,
                ),
                
                ft.Container(height=20),
                
                # Pilots list section
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Pilots List", size=18, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton(
                                "Refresh",
                                icon=ft.Icons.REFRESH,
                                on_click=self.refresh_pilots,
                                style=ft.ButtonStyle(bgcolor="#2196f3"),
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(
                            content=self.data_table,
                            expand=True,
                        ),
                    ]),
                    padding=20,
                    border=ft.border.all(1, "#e0e0e0"),
                    border_radius=10,
                    expand=True,
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def load_pilots(self):
        """Load pilots from database."""
        try:
            self.pilots = fetch_pilot_data_new(self.airline_id)
            self.update_table()
        except Exception as e:
            self.show_error("Database Error", f"Failed to load pilots: {str(e)}")

    def update_table(self):
        """Update the data table with current pilots."""
        self.data_table.rows.clear()
        
        for pilot in self.pilots:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(pilot.get('id', '')))),
                        ft.DataCell(ft.Text(pilot.get('name', ''))),
                        ft.DataCell(ft.Text(pilot.get('license_number', ''))),
                        ft.DataCell(ft.Text(pilot.get('rating', ''))),
                        ft.DataCell(ft.Text(str(pilot.get('hours', 0)))),
                        ft.DataCell(ft.Text(pilot.get('status', ''))),
                        ft.DataCell(ft.Text(pilot.get('home_hub', ''))),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Edit",
                                    on_click=lambda e, p=pilot: self.edit_pilot(p),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Delete",
                                    icon_color="#f44336",
                                    on_click=lambda e, p=pilot: self.delete_pilot_clicked(p),
                                ),
                            ]),
                        ),
                    ],
                )
            )
        
        self.page.update()

    def add_pilot_clicked(self, e):
        """Handle add pilot button click."""
        if not self.validate_form():
            return
        
        try:
            pilot_data = self.get_form_data()
            add_pilot(
                name=pilot_data['name'],
                license_number=pilot_data['license_number'],
                rating=pilot_data['rating'],
                hours=pilot_data['hours'],
                status=pilot_data['status'],
                home_hub=pilot_data['home_hub'],
                current_location=pilot_data['current_location'],
                airline_id=self.airline_id
            )
            
            self.show_success("Success", "Pilot added successfully!")
            self.clear_form(None)
            self.load_pilots()
            
        except Exception as ex:
            self.show_error("Error", f"Failed to add pilot: {str(ex)}")

    def update_pilot_clicked(self, e):
        """Handle update pilot button click."""
        if not self.selected_pilot:
            self.show_error("Error", "Please select a pilot to update")
            return
        
        if not self.validate_form():
            return
        
        try:
            pilot_data = self.get_form_data()
            update_pilot(
                pilot_id=self.selected_pilot['id'],
                name=pilot_data['name'],
                license_number=pilot_data['license_number'],
                rating=pilot_data['rating'],
                hours=pilot_data['hours'],
                status=pilot_data['status'],
                home_hub=pilot_data['home_hub'],
                current_location=pilot_data['current_location']
            )
            
            self.show_success("Success", "Pilot updated successfully!")
            self.clear_form(None)
            self.load_pilots()
            
        except Exception as ex:
            self.show_error("Error", f"Failed to update pilot: {str(ex)}")

    def delete_pilot_clicked(self, pilot):
        """Handle delete pilot button click."""
        def confirm_delete(e):
            if e.control.text == "Yes":
                try:
                    delete_pilot(pilot['id'])
                    self.show_success("Success", "Pilot deleted successfully!")
                    self.load_pilots()
                except Exception as ex:
                    self.show_error("Error", f"Failed to delete pilot: {str(ex)}")
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete pilot '{pilot['name']}'?"),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def edit_pilot(self, pilot):
        """Load pilot data into form for editing."""
        self.selected_pilot = pilot
        
        self.pilot_name.value = pilot.get('name', '')
        self.license_number.value = pilot.get('license_number', '')
        self.rating.value = pilot.get('rating', '')
        self.hours.value = str(pilot.get('hours', 0))
        self.status.value = pilot.get('status', '')
        self.home_hub.value = pilot.get('home_hub', '')
        self.current_location.value = pilot.get('current_location', '')
        
        self.page.update()

    def clear_form(self, e):
        """Clear the form fields."""
        self.selected_pilot = None
        self.pilot_name.value = ""
        self.license_number.value = ""
        self.rating.value = None
        self.hours.value = ""
        self.status.value = None
        self.home_hub.value = ""
        self.current_location.value = ""
        
        self.page.update()

    def refresh_pilots(self, e):
        """Refresh pilots list."""
        self.load_pilots()

    def validate_form(self):
        """Validate form inputs."""
        if not self.pilot_name.value or not self.pilot_name.value.strip():
            self.show_error("Validation Error", "Pilot name is required")
            return False
        
        if not self.license_number.value or not self.license_number.value.strip():
            self.show_error("Validation Error", "License number is required")
            return False
        
        if not self.rating.value:
            self.show_error("Validation Error", "Rating is required")
            return False
        
        try:
            hours = int(self.hours.value or 0)
            if hours < 0:
                self.show_error("Validation Error", "Flight hours must be non-negative")
                return False
        except ValueError:
            self.show_error("Validation Error", "Flight hours must be a valid number")
            return False
        
        if not self.status.value:
            self.show_error("Validation Error", "Status is required")
            return False
        
        return True

    def get_form_data(self):
        """Get form data as dictionary."""
        return {
            'name': self.pilot_name.value.strip(),
            'license_number': self.license_number.value.strip(),
            'rating': self.rating.value,
            'hours': int(self.hours.value or 0),
            'status': self.status.value,
            'home_hub': self.home_hub.value.strip().upper(),
            'current_location': self.current_location.value.strip().upper(),
        }

    def show_error(self, title: str, message: str):
        """Show error dialog."""
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

    def show_success(self, title: str, message: str):
        """Show success dialog."""
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