import requests
import json
import os
import time
import ollama
from datetime import datetime

# ─── DO THIS!!!───────────pip install ollama────────────────────────────────────────────────────────
# pip install ollama************************
def get_coordinates(location_name):
    """Look up coordinates for a location using OpenStreetMap"""
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={'q': location_name, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'HikePlanningAgent/1.0 (student@gmail.com)'},
            timeout=10
        )
        time.sleep(1)  # Respect Nominatim usage policy
        data = response.json()
        if data:
            return {'lat': float(data[0]['lat']), 'lon': float(data[0]['lon']), 'name': data[0]['display_name']}
        return {'error': 'Location not found'}
    except Exception as e:
        return {'error': str(e)}


def get_weather(latitude, longitude, days=7):
    """Get weather forecast for coordinates using Open-Meteo"""
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                'latitude': latitude,
                'longitude': longitude,
                'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_probability_max', 'windspeed_10m_max', 'weathercode'],
                'timezone': 'auto',
                'forecast_days': min(days, 7)
            },
            timeout=10
        )
        data = response.json()
        forecast = []
        weather_codes = {0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
                         51: 'Light drizzle', 61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
                         71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
                         95: 'Thunderstorm', 96: 'Thunderstorm with hail'}
        for i in range(len(data['daily']['time'])):
            forecast.append({
                'date': data['daily']['time'][i],
                'temp_max': data['daily']['temperature_2m_max'][i],
                'temp_min': data['daily']['temperature_2m_min'][i],
                'rain_chance': data['daily']['precipitation_probability_max'][i],
                'wind_speed': data['daily']['windspeed_10m_max'][i],
                'description': weather_codes.get(data['daily']['weathercode'][i], 'Unknown')
            })
        return {'forecast': forecast}
    except Exception as e:
        return {'error': str(e)}


def write_report(content, filename=None):
    """Save hiking plan to a text file"""
    try:
        os.makedirs("reports", exist_ok=True)
        if filename is None:
            filename = f"hike_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = f"reports/{filename}"
        with open(filepath, 'w') as f:
            f.write(content)
        return {'success': True, 'filepath': filepath}
    except Exception as e:
        return {'error': str(e)}


tool_map = {
    "get_coordinates": get_coordinates,
    "get_weather": get_weather,
    "write_report": write_report
}

# ─── TOOL DEFINITIONS ────────────────────────────────────────────────────────

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_coordinates",
            "description": "Look up latitude and longitude for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {"type": "string", "description": "Name of the location"}
                },
                "required": ["location_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather forecast for coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "days": {"type": "integer", "description": "Number of days to forecast (max 7)"}
                },
                "required": ["latitude", "longitude"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_report",
            "description": "Save the hiking plan to a text file",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "filename": {"type": "string"}
                },
                "required": ["content"]
            }
        }
    }
]

# ─── SYSTEM PROMPT ───────────────────────────────────────────────────────────

system_prompt = """You are HikePlanner AI, a friendly hiking trip planning assistant.

YOUR PROCESS:
1. Ask the user for their hike location, date and duration if not provided
2. Use get_coordinates to look up the location
3. Use get_weather to get the forecast for those coordinates
4. Give practical recommendations based on the weather:
   - Hot (>25°C): lots of water, sunscreen, hat, start early
   - Cold (<10°C): layers, thermal wear, gloves
   - Rain (>50%): waterproof jacket, extra socks
   - High winds (>30km/h): windproof jacket, avoid exposed ridges
5. Offer to save the plan using write_report

RULES:
- Never invent coordinates or weather - always use the tools
- Ask for clarification if information is missing
- Safety first - warn against hiking in dangerous conditions"""

# ─── AGENT ───────────────────────────────────────────────────────────────────

history = []

def chat(user_message):
    history.append({"role": "user", "content": user_message})
    messages = [{"role": "system", "content": system_prompt}] + history

    # Round 1: LLM decides which tool to call
    response = ollama.chat(model="qwen3:4b", messages=messages, tools=tools)

    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            name = tool.function.name
            args = tool.function.arguments
            print(f"[Tool called: {name}({args})]")
            try:
                result = tool_map[name](**args)
                history.append({"role": "tool", "content": json.dumps(result), "name": name})
            except Exception as e:
                history.append({"role": "tool", "content": json.dumps({"error": str(e)}), "name": name})

        # Round 2: LLM forms final answer using tool results
        final = ollama.chat(model="qwen3:4b", messages=messages + [response.message] + history[-len(response.message.tool_calls):])
        answer = final.message.content
    else:
        answer = response.message.content

    history.append({"role": "assistant", "content": answer})
    return answer

# ─── CHAT LOOP ────────────────────────────────────────────────────────────────

print("HikePlanner AI - type 'quit' to exit, 'reset' to start over")
while True:
    user_input = input("\nYou: ").strip()
    if user_input.lower() == "quit":
        break
    elif user_input.lower() == "reset":
        history.clear()
        print("Conversation reset.")
    elif user_input:
        print(f"Assistant: {chat(user_input)}")