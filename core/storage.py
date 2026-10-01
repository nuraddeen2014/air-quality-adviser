import json
import os


class LocationHistoryStore:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        os.makedirs(self.data_folder, exist_ok=True)

        self.readings_file = os.path.join(
            self.data_folder, "readings.json"
        )
        self.favourites_file = os.path.join(
            self.data_folder, "favourites.json"
        )
        self.advice_file = os.path.join(
            self.data_folder, "health_advice.json"
        )

    def _save_json(self, filename, data):
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)

    def _load_json(self, filename):
        if not os.path.exists(filename):
            return []

        with open(filename, "r") as file:
            return json.load(file)

    def save_reading(self, reading):
        readings = self._load_json(self.readings_file)
        readings.append(reading)
        self._save_json(self.readings_file, readings)

    def load_readings(self):
        return self._load_json(self.readings_file)

    def save_favourite(self, location):
        favourites = self._load_json(self.favourites_file)

        if location not in favourites:
            favourites.append(location)

        self._save_json(self.favourites_file, favourites)

    def load_favourites(self):
        return self._load_json(self.favourites_file)

    def save_health_advice(self, advice):
        health_advice = self._load_json(self.advice_file)
        health_advice.append(advice)
        self._save_json(self.advice_file, health_advice)

    def load_health_advice(self):
        return self._load_json(self.advice_file)