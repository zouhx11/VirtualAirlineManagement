import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from configparser import ConfigParser
import os

# Configuration file
CONFIG_FILE = "config.ini"

# Load or create configuration
config = ConfigParser()
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as file:
        config['PREFERENCES'] = {
            'theme': 'flatly',  # Default theme from ttkbootstrap
            'data_refresh_rate': '30'
        }
        config.write(file)
config.read(CONFIG_FILE)

# Ensure 'PREFERENCES' section exists
if 'PREFERENCES' not in config:
    config['PREFERENCES'] = {
        'theme': 'flatly',  # Default theme
        'data_refresh_rate': '30'
    }
    with open(CONFIG_FILE, 'w') as file:
        config.write(file)

def save_preferences(theme, refresh_rate):
    """Save preferences to the configuration file."""
    config['PREFERENCES']['theme'] = theme
    config['PREFERENCES']['data_refresh_rate'] = refresh_rate
    with open(CONFIG_FILE, 'w') as file:
        config.write(file)
    Messagebox.show_info("Success", "Preferences saved successfully!")

def open_settings(main_window):
    """Open the settings GUI."""
    def save():
        selected_theme = theme_var.get()
        refresh_rate = refresh_rate_var.get()
        save_preferences(selected_theme, refresh_rate)
        settings_window.destroy()  # Close the window after saving
        main_window.style.theme_use(selected_theme)  # Apply the selected theme

    settings_window = ttk.Toplevel()
    settings_window.title("Settings")

    frame = ttk.Frame(settings_window, padding=20)
    frame.pack(fill=BOTH, expand=True)

    # Theme selection
    theme_label = ttk.Label(frame, text="Select Theme:", font=("Helvetica", 12))
    theme_label.grid(row=0, column=0, sticky="w", pady=5)

    available_themes = [
        "flatly", "darkly", "litera", "minty", "sandstone", "united", "solar",
        "journal", "cosmo", "cyborg", "pulse", "lumen", "materia", "simplex",
        "superhero", "yeti", "morph"
    ]
    theme_var = ttk.StringVar(value=config['PREFERENCES'].get('theme', 'flatly'))
    theme_dropdown = ttk.Combobox(frame, textvariable=theme_var, values=available_themes)
    theme_dropdown.grid(row=0, column=1, pady=5)

    # Data refresh rate
    refresh_rate_label = ttk.Label(frame, text="Data Refresh Rate (s):", font=("Helvetica", 12))
    refresh_rate_label.grid(row=1, column=0, sticky="w", pady=5)

    refresh_rate_var = ttk.StringVar(value=config['PREFERENCES'].get('data_refresh_rate', '30'))
    refresh_rate_entry = ttk.Entry(frame, textvariable=refresh_rate_var)
    refresh_rate_entry.grid(row=1, column=1, pady=5)

    # Save button
    save_button = ttk.Button(frame, text="Save", bootstyle=SUCCESS, command=save)
    save_button.grid(row=2, column=0, columnspan=2, pady=10)

if __name__ == "__main__":
    main_window = ttk.Window(themename=config['PREFERENCES'].get('theme', 'flatly'))
    open_settings(main_window)
    main_window.mainloop()
