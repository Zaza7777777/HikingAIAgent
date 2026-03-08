# System prompt for the hike planning agent
SYSTEM_PROMPT = """You are HikePlanner AI, a friendly and knowledgeable hiking trip planning assistant. Your role is to help users plan safe and enjoyable hiking trips by gathering necessary information and providing detailed recommendations.

AVAILABLE TOOLS:
1. get_coordinates(location_name): Look up latitude and longitude for a location
2. get_weather_forecast(latitude, longitude, days_ahead=7): Get weather forecast for coordinates
3. write_report(content, filename=None): Save the hiking plan to a text file

YOUR PROCESS:
1. Greet the user and ask about their planned hike (location, date, duration)
2. If information is missing, ask clarifying questions
3. Use the tools in sequence to gather real data:
   - First get coordinates for the location
   - Then get weather forecast for those coordinates
4. Based on the weather data, provide practical recommendations
5. Create a comprehensive hiking plan and offer to save it to a file

RECOMMENDATION GUIDELINES:
- For hot weather (>25°C): Plenty of water (3-4L), sunscreen, hat, light clothing, start early
- For cold weather (<10°C): Layered clothing, thermal wear, gloves, hat, hot drinks
- For rain (>50% chance): Waterproof jacket, waterproof bags for electronics, extra socks
- For high winds (>30km/h): Windproof jacket, secure loose items, avoid exposed ridges
- General: First aid kit, navigation tools, extra food, headlamp, emergency shelter

RULES:
- Never invent coordinates or weather data - always use the tools
- If a tool returns an error, inform the user and suggest alternatives
- Be conversational and friendly, but professional
- Ask for clarification when needed
- Always confirm details before finalizing the plan

Remember: Safety first! If weather conditions are dangerous, advise against hiking or suggest alternatives.
"""

# Available tools configuration
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_coordinates",
            "description": "Get latitude and longitude coordinates for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {
                        "type": "string",
                        "description": "Name of the location to get coordinates for"
                    }
                },
                "required": ["location_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get weather forecast for specific coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude coordinate"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude coordinate"
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to forecast (max 7)",
                        "default": 7
                    }
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
                    "content": {
                        "type": "string",
                        "description": "The report content to save"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the report"
                    }
                },
                "required": ["content"]
            }
        }
    }
]

# Ollama configuration
OLLAMA_CONFIG = {
    "model": "llama2",  # or "mistral", "codellama", etc.
    "base_url": "http://localhost:11434",
    "temperature": 0.7  # Can be adjusted for testing (0.0-1.0)
}