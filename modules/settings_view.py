import flet as ft
from core.config_manager import ConfigManager


class SettingsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.config_manager = ConfigManager()
        
    def show_dialog(self):
        """Show settings dialog."""
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Settings"),
            content=ft.Column([
                ft.Text("Application Settings", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Settings configuration coming soon!"),
                ft.Container(height=20),
                ft.Text("Current theme: Light"),
                ft.Text("Database: Connected"),
            ], height=200),
            actions=[ft.TextButton("Close", on_click=close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()