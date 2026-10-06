"""
risk_logic.py
Domain Logic & Risk Analyzer for the Air Quality Advisor app.

Pure logic only: no API calls, no UI. Other modules pass in air quality data
and a user profile, and get back a structured risk assessment.

Typical use:
    from risk_logic import analyze_risk

    result = analyze_risk(
        pollutants={"pm25": 40.0, "ozone": 60.0, "no2": 30.0},
        profile={"age_group": "child", "has_respiratory_condition": True},
    )
    print(result["level"], result["outdoor_safe"], result["advice"])

Units:
    pm25  -> micrograms per cubic metre (ug/m3)
    ozone -> parts per billion (ppb), 8-hour average
    no2   -> parts per billion (ppb), 1-hour average
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# AQI categories (US EPA scale)
# ---------------------------------------------------------------------------

AQI_CATEGORIES = [
    (50, "Good"),
    (100, "Moderate"),
    (150, "Unhealthy for Sensitive Groups"),
    (200, "Unhealthy"),
    (300, "Very Unhealthy"),
    (500, "Hazardous"),
]

# ---------------------------------------------------------------------------
# Pollutant breakpoints: (conc_low, conc_high, aqi_low, aqi_high)
# ---------------------------------------------------------------------------

BREAKPOINTS = {
    "pm25": [
        (0.0, 9.0, 0, 50),
        (9.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 125.4, 151, 200),
        (125.5, 225.4, 201, 300),
        (225.5, 325.4, 301, 500),
    ],
    "ozone": [
        (0, 54, 0, 50),
        (55, 70, 51, 100),
        (71, 85, 101, 150),
        (86, 105, 151, 200),
        (106, 200, 201, 300),
    ],
    "no2": [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 2049, 301, 500),
    ],
}

POLLUTANT_NAMES = {
    "pm25": "PM2.5 (fine particles)",
    "ozone": "ozone",
    "no2": "nitrogen dioxide",
}

POLLUTANT_NOTES = {
    "pm25": "Fine particles can get deep into the lungs and bloodstream.",
    "ozone": "Ozone irritates the airways and is worst on hot, sunny afternoons.",
    "no2": "Nitrogen dioxide comes mostly from traffic and can inflame the airways.",
}

# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

SENSITIVE_AGE_GROUPS = {"child", "older_adult"}
VALID_AGE_GROUPS = {"child", "adult", "older_adult"}

# Highest AQI at which outdoor activity is still considered OK.
SAFE_AQI_GENERAL = 100
SAFE_AQI_SENSITIVE = 50


@dataclass
class UserProfile:
    age_group: str = "adult"  # "child", "adult", "older_adult"
    has_respiratory_condition: bool = False  # asthma, COPD, etc.

    def __post_init__(self):
        if self.age_group not in VALID_AGE_GROUPS:
            raise ValueError(
                f"age_group must be one of {sorted(VALID_AGE_GROUPS)}, "
                f"got {self.age_group!r}"
            )

    @property
    def is_sensitive(self) -> bool:
        return self.has_respiratory_condition or self.age_group in SENSITIVE_AGE_GROUPS


def _to_profile(profile) -> UserProfile:
    """Accept a UserProfile, a dict, or None."""
    if profile is None:
        return UserProfile()
    if isinstance(profile, UserProfile):
        return profile
    if isinstance(profile, dict):
        return UserProfile(
            age_group=profile.get("age_group", "adult"),
            has_respiratory_condition=bool(profile.get("has_respiratory_condition", False)),
        )
    raise TypeError("profile must be a UserProfile, dict, or None")


# ---------------------------------------------------------------------------
# AQI calculations
# ---------------------------------------------------------------------------


def calculate_sub_index(pollutant: str, concentration: float) -> Optional[int]:
    """Convert one pollutant concentration into an AQI sub-index.

    Returns None if the pollutant is unknown or the value is missing/negative.
    Values above the top breakpoint are capped at 500.
    """
    if pollutant not in BREAKPOINTS or concentration is None or concentration < 0:
        return None

    table = BREAKPOINTS[pollutant]
    for c_lo, c_hi, i_lo, i_hi in table:
        if concentration <= c_hi:
            # Values that fall in the small gap between breakpoints snap up
            c = max(concentration, c_lo)
            return round((i_hi - i_lo) / (c_hi - c_lo) * (c - c_lo) + i_lo)
    return 500


def get_aqi_category(aqi: int) -> str:
    """Return the EPA category name for an AQI value."""
    if aqi < 0:
        raise ValueError("AQI cannot be negative")
    for upper, name in AQI_CATEGORIES:
        if aqi <= upper:
            return name
    return "Hazardous"


def calculate_aqi(pollutants: Dict[str, float]):
    """Overall AQI is the highest sub-index among the pollutants.

    Returns (aqi, dominant_pollutant, sub_indices). If no usable data is
    given, returns (None, None, {}).
    """
    sub_indices = {}
    for name, value in pollutants.items():
        idx = calculate_sub_index(name, value)
        if idx is not None:
            sub_indices[name] = idx

    if not sub_indices:
        return None, None, {}

    dominant = max(sub_indices, key=sub_indices.get)
    return sub_indices[dominant], dominant, sub_indices


# ---------------------------------------------------------------------------
# Risk analysis
# ---------------------------------------------------------------------------


def _activity_guidance(aqi: int, sensitive: bool) -> Dict[str, str]:
    """Plain-language activity advice based on AQI and sensitivity."""
    if sensitive:
        if aqi <= 50:
            return {"outdoor": "Safe", "advice": "Air quality is good. Enjoy normal outdoor activity."}
        if aqi <= 100:
            return {
                "outdoor": "Caution",
                "advice": "Outdoor activity is generally fine, but watch for coughing, "
                          "wheezing, or shortness of breath. Keep any rescue medication handy.",
            }
        if aqi <= 150:
            return {
                "outdoor": "Limit",
                "advice": "Limit long or intense outdoor activity. Take breaks, "
                          "and choose indoor exercise if you feel symptoms.",
            }
        if aqi <= 200:
            return {
                "outdoor": "Avoid",
                "advice": "Avoid outdoor exertion. Stay indoors with windows closed "
                          "and use an air purifier if you have one.",
            }
        return {
            "outdoor": "Avoid",
            "advice": "Stay indoors. Health risk is serious. Avoid all outdoor "
                      "activity and follow your doctor's action plan if you have one.",
        }

    # General population
    if aqi <= 50:
        return {"outdoor": "Safe", "advice": "Air quality is good. Enjoy outdoor activities."}
    if aqi <= 100:
        return {"outdoor": "Safe", "advice": "Air quality is acceptable. Unusually sensitive people may notice mild effects."}
    if aqi <= 150:
        return {"outdoor": "Caution", "advice": "Most people are fine, but consider shorter or lighter outdoor exercise."}
    if aqi <= 200:
        return {"outdoor": "Limit", "advice": "Reduce prolonged or heavy outdoor exertion. Take more breaks."}
    if aqi <= 300:
        return {"outdoor": "Avoid", "advice": "Avoid outdoor exertion. Move activities indoors."}
    return {"outdoor": "Avoid", "advice": "Health emergency conditions. Everyone should stay indoors."}


def analyze_risk(pollutants: Dict[str, float], profile=None, aqi_override: Optional[int] = None) -> dict:
    """Main entry point. Analyse air quality for a given user.

    Args:
        pollutants: e.g. {"pm25": 40.0, "ozone": 60.0, "no2": 30.0}
        profile: UserProfile, dict, or None (treated as healthy adult)
        aqi_override: use this AQI if an API already provides one (the
            dominant pollutant is still worked out from `pollutants`).

    Returns a dict with:
        aqi, level, dominant_pollutant, sub_indices, is_sensitive,
        outdoor_safe (bool), outdoor_status, advice, pollutant_notes,
        sensitive_warning
    """
    user = _to_profile(profile)
    calc_aqi, dominant, sub_indices = calculate_aqi(pollutants or {})
    aqi = aqi_override if aqi_override is not None else calc_aqi

    if aqi is None:
        return {
            "aqi": None,
            "level": "Unknown",
            "dominant_pollutant": None,
            "sub_indices": {},
            "is_sensitive": user.is_sensitive,
            "outdoor_safe": False,
            "outdoor_status": "Unknown",
            "advice": "No valid air quality data available. Check again later.",
            "pollutant_notes": [],
            "sensitive_warning": None,
        }

    level = get_aqi_category(aqi)
    guidance = _activity_guidance(aqi, user.is_sensitive)
    threshold = SAFE_AQI_SENSITIVE if user.is_sensitive else SAFE_AQI_GENERAL

    # Short notes for pollutants that are at Moderate or worse
    notes = [
        f"{POLLUTANT_NAMES[p].capitalize()}: {POLLUTANT_NOTES[p]}"
        for p, idx in sorted(sub_indices.items(), key=lambda kv: -kv[1])
        if idx > 50
    ]

    sensitive_warning = None
    if not user.is_sensitive and 100 < aqi <= 150:
        sensitive_warning = (
            "Children, older adults, and people with asthma or lung conditions "
            "should limit outdoor activity today."
        )

    return {
        "aqi": aqi,
        "level": level,
        "dominant_pollutant": dominant,
        "sub_indices": sub_indices,
        "is_sensitive": user.is_sensitive,
        "outdoor_safe": aqi <= threshold,
        "outdoor_status": guidance["outdoor"],
        "advice": guidance["advice"],
        "pollutant_notes": notes,
        "sensitive_warning": sensitive_warning,
    }


def analyze_forecast(forecast: List[dict], profile=None) -> List[dict]:
    """Analyse a list of forecast entries.

    Each entry: {"time": "2026-10-02 09:00", "pollutants": {...}}
    (an optional "aqi" key is used as the override).
    Returns the same list with an "analysis" key added to each entry.
    """
    results = []
    for entry in forecast:
        analysis = analyze_risk(
            entry.get("pollutants", {}),
            profile,
            aqi_override=entry.get("aqi"),
        )
        results.append({**entry, "analysis": analysis})
    return results


def find_best_time_outdoors(forecast: List[dict], profile=None) -> Optional[dict]:
    """Return the forecast entry with the lowest AQI, or None if no data."""
    analysed = [e for e in analyze_forecast(forecast, profile) if e["analysis"]["aqi"] is not None]
    if not analysed:
        return None
    return min(analysed, key=lambda e: e["analysis"]["aqi"])


# ---------------------------------------------------------------------------
# Quick manual test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample = {"pm25": 40.0, "ozone": 60.0, "no2": 30.0}

    for label, prof in [
        ("Healthy adult", {"age_group": "adult"}),
        ("Child with asthma", {"age_group": "child", "has_respiratory_condition": True}),
    ]:
        r = analyze_risk(sample, prof)
        print(f"--- {label} ---")
        print(f"AQI {r['aqi']} ({r['level']}), main pollutant: {r['dominant_pollutant']}")
        print(f"Outdoor: {r['outdoor_status']} | safe: {r['outdoor_safe']}")
        print(r["advice"])
        print()
