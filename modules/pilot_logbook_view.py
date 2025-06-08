import flet as ft


class PilotLogbookView:
    def __init__(self, page: ft.Page):
        self.page = page
        
    def build(self):
        """Build the pilot logbook interface."""
        return ft.Column([
            ft.Text("Pilot Logbook", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Track flight records and pilot experience", size=16, color="#616161"),
            ft.Divider(),
            ft.Container(
                content=ft.Text("Pilot Logbook - Coming Soon!"),
                alignment=ft.alignment.center,
                expand=True,
            ),
        ], expand=True)