import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from core.config_manager import ConfigManager

CONFIG_FILE = "config.ini"

def open_settings(main_window):
    """Open the settings GUI and allow user to modify preferences."""
    config_manager = ConfigManager(CONFIG_FILE)

    # Retrieve current preferences
    current_theme = config_manager.get_preference('theme', 'flatly')
    current_refresh_rate = config_manager.get_preference('data_refresh_rate', '30')

    def save():
        selected_theme = theme_var.get()
        refresh_rate = refresh_rate_var.get()

        # Validate the refresh rate input if necessary
        # For example, ensure it is an integer
        try:
            int(refresh_rate)
        except ValueError:
            Messagebox.show_error("Data refresh rate must be an integer.", "Error")
            return

        # Save preferences
        config_manager.set_preference('theme', selected_theme)
        config_manager.set_preference('data_refresh_rate', refresh_rate)

        Messagebox.show_info("Preferences saved successfully!", "Success")
        settings_window.destroy()

        # Apply the selected theme
        main_window.style.theme_use(selected_theme)

    # Create the settings window
    settings_window = ttk.Toplevel()
    settings_window.title("Settings")

    frame = ttk.Frame(settings_window, padding=20)
    frame.pack(fill=ttk.BOTH, expand=True)

    # Available themes
    available_themes = [
        "flatly", "darkly", "litera", "minty", "sandstone", "united", "solar",
        "journal", "cosmo", "cyborg", "pulse", "lumen", "materia", "simplex",
        "superhero", "yeti", "morph"
    ]

    # Theme selection
    ttk.Label(frame, text="Select Theme:", font=("Helvetica", 12)).grid(row=0, column=0, sticky="w", pady=5)
    theme_var = ttk.StringVar(value=current_theme)
    theme_dropdown = ttk.Combobox(frame, textvariable=theme_var, values=available_themes, state="readonly")
    theme_dropdown.grid(row=0, column=1, pady=5, padx=(5, 0))

    # Data refresh rate
    ttk.Label(frame, text="Data Refresh Rate (s):", font=("Helvetica", 12)).grid(row=1, column=0, sticky="w", pady=5)
    refresh_rate_var = ttk.StringVar(value=current_refresh_rate)
    refresh_rate_entry = ttk.Entry(frame, textvariable=refresh_rate_var)
    refresh_rate_entry.grid(row=1, column=1, pady=5, padx=(5, 0))

    # Save button
    save_button = ttk.Button(frame, text="Save", bootstyle=SUCCESS, command=save)
    save_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Focus on theme dropdown for convenience
    theme_dropdown.focus_set()

if __name__ == "__main__":
    # If running this file directly for testing, instantiate a main window and open settings
    config_manager = ConfigManager(CONFIG_FILE)
    current_theme = config_manager.get_preference('theme', 'flatly')
    main_window = ttk.Window(themename=current_theme)
    open_settings(main_window)
    main_window.mainloop()
