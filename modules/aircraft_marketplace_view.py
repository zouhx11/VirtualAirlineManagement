import flet as ft


class AircraftMarketplaceView:
    def __init__(self, page: ft.Page):
        self.page = page
        
    def build(self):
        """Build the aircraft marketplace interface."""
        return ft.Column([
            ft.Text("Aircraft Marketplace", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Buy and lease aircraft for your fleet", size=16, color="#616161"),
            ft.Divider(),
            ft.Container(
                content=ft.Text("Aircraft Marketplace - Coming Soon!"),
                alignment=ft.alignment.center,
                expand=True,
            ),
        ], expand=True)