import flet as ft


class ScheduleView:
    def __init__(self, page: ft.Page, airline_id: int):
        self.page = page
        self.airline_id = airline_id
        
    def build(self):
        """Build the schedule interface."""
        return ft.Column([
            ft.Text("Flight Schedules", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Plan and manage flight schedules", size=16, color="#616161"),
            ft.Divider(),
            ft.Container(
                content=ft.Text("Flight Schedules - Coming Soon!"),
                alignment=ft.alignment.center,
                expand=True,
            ),
        ], expand=True)