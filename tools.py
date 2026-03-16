import requests
import json
from typing import Tuple, Optional, Dict
from datetime import datetime, timedelta
import time


class GeocodingTool:
    """Tool to look up coordinates for a location using Nominatim (OpenStreetMap)"""

    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'HikePlanningAgent/1.0 (meowwoof@example.com)'
        }



    def get_coordinates(self, location_name: str) -> Optional[Dict]:
        """
        Get coordinates for a location name

        Args:
            location_name: Name of the location (e.g., "Mount Everest Base Camp")

        Returns:
            Dictionary with lat, lon, display_name or None if not found
        """
        try:
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            # Respect Nominatim's usage policy
            time.sleep(1)

            data = response.json()
            if data and len(data) > 0:
                return {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon']),
                    'display_name': data[0]['display_name']
                }
            return None

        except requests.exceptions.RequestException as e:
            return {'error': f"Geocoding API error: {str(e)}"}
        except (ValueError, KeyError) as e:
            return {'error': f"Error parsing geocoding response: {str(e)}"}


class WeatherTool:
    """Tool to get weather forecast using Open-Meteo API"""

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    def get_forecast(
            self,
            latitude: float,
            longitude: float,
            days_ahead: int = 7
    ) -> Optional[Dict]:
        """
        Get weather forecast for coordinates

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days_ahead: Number of days to forecast (max 7)

        Returns:
            Dictionary with weather data or error message
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'daily': [
                    'temperature_2m_max',
                    'temperature_2m_min',
                    'precipitation_probability_max',
                    'windspeed_10m_max',
                    'weathercode'
                ],
                'timezone': 'auto',
                'forecast_days': min(days_ahead, 7)
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Translate weather codes to descriptions
            weather_codes = {
                0: 'Clear sky',
                1: 'Mainly clear',
                2: 'Partly cloudy',
                3: 'Overcast',
                45: 'Fog',
                48: 'Rime fog',
                51: 'Light drizzle',
                53: 'Moderate drizzle',
                55: 'Dense drizzle',
                61: 'Slight rain',
                63: 'Moderate rain',
                65: 'Heavy rain',
                71: 'Slight snow',
                73: 'Moderate snow',
                75: 'Heavy snow',
                77: 'Snow grains',
                80: 'Slight rain showers',
                81: 'Moderate rain showers',
                82: 'Violent rain showers',
                85: 'Slight snow showers',
                86: 'Heavy snow showers',
                95: 'Thunderstorm',
                96: 'Thunderstorm with slight hail',
                99: 'Thunderstorm with heavy hail'
            }

            # Format the forecast
            forecast = []
            for i in range(len(data['daily']['time'])):
                weather_code = data['daily']['weathercode'][i]
                forecast.append({
                    'date': data['daily']['time'][i],
                    'temp_max': data['daily']['temperature_2m_max'][i],
                    'temp_min': data['daily']['temperature_2m_min'][i],
                    'precipitation_prob': data['daily']['precipitation_probability_max'][i],
                    'wind_speed': data['daily']['windspeed_10m_max'][i],
                    'weather_description': weather_codes.get(weather_code, 'Unknown'),
                    'weather_code': weather_code
                })

            return {
                'latitude': latitude,
                'longitude': longitude,
                'forecast': forecast,
                'units': {
                    'temperature': '°C',
                    'wind_speed': 'km/h',
                    'precipitation': '%'
                }
            }

        except requests.exceptions.RequestException as e:
            return {'error': f"Weather API error: {str(e)}"}
        except (ValueError, KeyError) as e:
            return {'error': f"Error parsing weather response: {str(e)}"}


class ReportWriter:
    """Tool to write the hiking plan to a text file"""

    def __init__(self, report_dir: str = "reports"):
        self.report_dir = report_dir
        import os
        os.makedirs(report_dir, exist_ok=True)

    def write_report(self, content: str, filename: str = None) -> Dict:
        """
        Write content to a text file

        Args:
            content: The report content to write
            filename: Optional filename, auto-generated if not provided

        Returns:
            Dictionary with status and filepath
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"hike_plan_{timestamp}.txt"

            filepath = f"{self.report_dir}/{filename}"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'success': True,
                'filepath': filepath,
                'message': f"Report successfully saved to {filepath}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Error writing report: {str(e)}"
            }