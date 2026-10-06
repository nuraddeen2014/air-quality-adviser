import requests

def fetch_air_quality(city_name):
    """
    Fetches air quality data from Open-Meteo.
    Returns a dictionary of data, or an error message if it fails.
    """
    try:
        # Step 1: Get Latitude and Longitude for the city
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&format=json"
        geo_response = requests.get(geo_url, timeout=5)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        
        if "results" not in geo_data:
            return {"error": "City not found."}
            
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        
        # Step 2: Fetch Air Quality using those coordinates
        aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=european_aqi,pm10,pm2_5,nitrogen_dioxide,ozone"
        aqi_response = requests.get(aqi_url, timeout=5)
        aqi_response.raise_for_status()
        
        return aqi_response.json()

    except requests.exceptions.Timeout:
        return {"error": "Connection timed out. Please check your internet."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error occurred: {e}"}