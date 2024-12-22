from configparser import ConfigParser
import os

class ConfigManager:
    _instance = None

    def __new__(cls, config_file="config.ini"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config_file = config_file
            cls._instance.config = ConfigParser()
            cls._instance.reload()
        return cls._instance

    def reload(self):
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        self.config.read(self.config_file)
        if 'DATABASES' not in self.config:
            self.config['DATABASES'] = {}
        if 'PREFERENCES' not in self.config:
            self.config['PREFERENCES'] = {}

    def get_database_path(self, db_key='userdata') -> str:
        return self.config['DATABASES'].get(db_key, 'user_data.db')

    def get_preference(self, key: str, default=None):
        return self.config['PREFERENCES'].get(key, default)

    def set_preference(self, key: str, value):
        self.config['PREFERENCES'][key] = str(value)
        self.save()

    def save(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_aeroapi_credentials(self, key: str, default=None):
        return self.config["AeroAPI"].get(key, default)
        