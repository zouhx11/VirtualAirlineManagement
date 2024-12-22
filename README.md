# Virtual Airline Management

Virtual Airline Management is a Python-based application designed to simulate and manage the operations of a virtual airline. It offers functionalities for managing pilots, fleets, flight schedules, and more, providing a comprehensive dashboard for monitoring and administration.

## Features

- **Pilot Management:** Add, edit, and remove pilots from your virtual airline.
- **Fleet Management:** Manage your aircraft fleet, including adding new aircraft and tracking existing ones.
- **Flight Scheduling:** Integrate with [FlightAware AeroAPI](https://flightaware.com/commercial/aeroapi/) to fetch and display real-time flight schedules based on the current location.
- **Pilot Logbook:** Keep track of pilot flight logs and history.
- **Dashboard:** Interactive dashboard to monitor airline performance and metrics.

## Installation

### Prerequisites

- **Python 3.8+**: Ensure Python is installed on your system. You can download it from [python.org](https://www.python.org/).
- **FlightAware AeroAPI Account**: Sign up for an account to obtain your `API_KEY` and `API_SECRET`.

### Setup Steps

1. **Clone the Repository:**

   ```sh
   git clone https://github.com/yourusername/VirtualAirlineManagement.git
   cd VirtualAirlineManagement
   ```
2. **Create a Virtual Environment:**
   ```sh
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**
    - Windows:
    ```sh
    venv\Scripts\activate
    ```

    - Linux/MacOS:
    ```sh
    source venv/bin/activate
    ```
4. **Upgrade pip:**
    ```sh
    pip install --upgrade pip
    ```

5. **Install Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

6. **Configure the Application:**

    Update the config.ini file with your AeroAPI credentials and other configurations.
    ```sh
    [AeroAPI]
    api_key = YOUR_API_KEY
    api_secret = YOUR_API_SECRET
    current_location = YOUR_CURRENT_LOCATION
    ```

7. **Run the Application:**

### Usage
Once the application is running, you can navigate through the GUI to manage different aspects of your virtual airline:

- **Pilot Management:** Add or remove pilots.
- **Fleet Management:** Manage your aircraft fleet.
- **Flight Schedules:** View and schedule flights using AeroAPI integration.
- **Pilot Logbook:** Access and manage pilot flight logs.
- **Dashboard:** View comprehensive analytics and metrics.

### Project Structure
```
VirtualAirlineManagement/
├── __pycache__/
├── .gitignore
├── .vscode/
│   └── settings.json
├── application.log
├── [config.ini](config.ini)
├── core/
│   ├── __pycache__/
│   ├── [config_manager.py](core/config_manager.py)
│   ├── [database_utils.py](core/database_utils.py)
│   ├── [settings.py](core/settings.py)
│   └── [utils.py](core/utils.py)
├── Database_Utils.log
├── icons/
├── [instructions.md](instructions.md)
├── [main.py](main.py)
├── modules/
│   ├── __pycache__/
│   ├── [fleet_management.py](modules/fleet_management.py)
│   ├── [pilot_dashboard.py](modules/pilot_dashboard.py)
│   ├── [pilot_logbook.py](modules/pilot_logbook.py)
│   ├── [pilot_management_gui.py](modules/pilot_management_gui.py)
│   └── [schedule.py](modules/schedule.py)
├── pilot_logbook.log
├── [README.md](README.md)
├── [requirements.txt](requirements.txt)
├── scripts/
│   ├── [create_pilots_table.py](scripts/create_pilots_table.py)
│   ├── [test_fetch_logbook_data.py](scripts/test_fetch_logbook_data.py)
│   └── ...
├── tests/
│   └── ...
├── venv/
│   └── ...
└── [VirtualAirlineManagement.code-workspace](VirtualAirlineManagement.code-workspace)
```
