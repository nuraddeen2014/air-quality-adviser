# models.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional


@dataclass
class AirReading:
    city: str
    latitude: float = 0.0
    longitude: float = 0.0
    pm2_5: Optional[float] = None
    pm10: Optional[float] = None
    nitrogen_dioxide: Optional[float] = None
    ozone: Optional[float] = None
    european_aqi: Optional[int] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def from_open_meteo(cls, city_name: str, raw_data: dict) -> "AirReading":
        """Factory method to safely build AirReading from Open-Meteo dictionary."""
        latitude = 0.0
        longitude = 0.0

        # Safely extract coordinates whether in geocoding results or root payload
        results = raw_data.get("results")
        if isinstance(results, list) and len(results) > 0:
            latitude = results[0].get("latitude", 0.0)
            longitude = results[0].get("longitude", 0.0)
        else:
            latitude = raw_data.get("latitude", 0.0)
            longitude = raw_data.get("longitude", 0.0)

        # Extract pollutant metrics
        current = raw_data.get("current", {})

        return cls(
            city=city_name,
            latitude=latitude,
            longitude=longitude,
            pm2_5=current.get("pm2_5"),
            pm10=current.get("pm10"),
            nitrogen_dioxide=current.get("nitrogen_dioxide"),
            ozone=current.get("ozone"),
            european_aqi=current.get("european_aqi"),
        )

    def to_pollutant_dict(self) -> Dict[str, float]:
        """Maps attributes to key names expected by risk_logic.py."""
        pollutants = {}
        if self.pm2_5 is not None:
            pollutants["pm25"] = float(self.pm2_5)
        if self.pm10 is not None:
            pollutants["pm10"] = float(self.pm10)
        if self.nitrogen_dioxide is not None:
            pollutants["no2"] = float(self.nitrogen_dioxide)
        if self.ozone is not None:
            pollutants["ozone"] = float(self.ozone)
        return pollutants

    def to_dict(self) -> dict:
        """Converts instance to a standard python dictionary."""
        return asdict(self)
