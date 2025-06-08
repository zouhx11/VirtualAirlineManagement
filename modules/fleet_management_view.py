import flet as ft


class FleetManagementView:
    def __init__(self, page: ft.Page, airline_id: int):
        self.page = page
        self.airline_id = airline_id
        
    def build(self):
        """Build the fleet management interface."""
        return ft.Column([
            ft.Text("Fleet Management", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Manage your aircraft fleet", size=16, color="#616161"),
            ft.Divider(),
            ft.Container(
                content=ft.Text("Fleet Management - Coming Soon!"),
                alignment=ft.alignment.center,
                expand=True,
            ),
        ], expand=True)