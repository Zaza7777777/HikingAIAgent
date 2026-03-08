import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from tools import GeocodingTool, WeatherTool, ReportWriter
from config import SYSTEM_PROMPT, TOOLS, OLLAMA_CONFIG


class HikePlanningAgent:
    def __init__(self, model: str = None, temperature: float = None):
        self.model = model or OLLAMA_CONFIG["model"]
        self.temperature = temperature or OLLAMA_CONFIG["temperature"]
        self.base_url = OLLAMA_CONFIG["base_url"]

        # Initialize tools
        self.geocoder = GeocodingTool()
        self.weather = WeatherTool()
        self.report_writer = ReportWriter()

        # Conversation history
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Store tool results for context
        self.tool_results = {}

    def chat_completion(self, messages: List[Dict]) -> Dict:
        """Send request to Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "message": {
                    "content": f"Error communicating with Ollama: {str(e)}"
                }
            }

    def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Execute a tool based on name and arguments"""
        try:
            if tool_name == "get_coordinates":
                result = self.geocoder.get_coordinates(arguments["location_name"])
                if result and "error" not in result:
                    # Store for later use
                    self.tool_results["last_coordinates"] = result
                return {"result": result}

            elif tool_name == "get_weather_forecast":
                result = self.weather.get_forecast(
                    arguments["latitude"],
                    arguments["longitude"],
                    arguments.get("days_ahead", 7)
                )
                if result and "error" not in result:
                    self.tool_results["last_weather"] = result
                return {"result": result}

            elif tool_name == "write_report":
                result = self.report_writer.write_report(
                    arguments["content"],
                    arguments.get("filename")
                )
                return {"result": result}

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": f"Error executing {tool_name}: {str(e)}"}

    def process_tool_calls(self, response_message: Dict) -> List[Dict]:
        """Process any tool calls in the response"""
        tool_calls = response_message.get("tool_calls", [])
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])

            print(f"\n🔧 Calling tool: {tool_name}")
            print(f"📥 Arguments: {arguments}")

            # Execute the tool
            result = self.execute_tool(tool_name, arguments)

            print(f"📤 Result: {json.dumps(result, indent=2)[:200]}...")

            # Add tool response to messages
            tool_response = {
                "role": "tool",
                "content": json.dumps(result),
                "name": tool_name
            }
            results.append(tool_response)

        return results

    def generate_hiking_plan(self, user_input: str) -> str:
        """Process user input and generate response"""

        # Add user message to history
        self.messages.append({"role": "user", "content": user_input})

        # Get response from LLM
        response = self.chat_completion(self.messages)

        if "message" not in response:
            return "I'm having trouble connecting to the language model. Please check if Ollama is running."

        assistant_message = response["message"]

        # Process any tool calls
        if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
            tool_responses = self.process_tool_calls(assistant_message)

            # Add assistant's tool call message to history
            self.messages.append(assistant_message)

            # Add all tool responses
            self.messages.extend(tool_responses)

            # Get final response from LLM with tool results
            final_response = self.chat_completion(self.messages)
            final_content = final_response.get("message", {}).get("content", "")

            # Add final response to history
            self.messages.append({"role": "assistant", "content": final_content})

            return final_content
        else:
            # No tool calls, just return the content
            content = assistant_message.get("content", "")
            self.messages.append({"role": "assistant", "content": content})
            return content

    def reset_conversation(self):
        """Reset the conversation history"""
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.tool_results = {}


def main():
    """Main chat loop"""
    print("=" * 60)
    print("🥾 HIKE PLANNER AI - Your Personal Hiking Assistant")
    print("=" * 60)
    print("\nWelcome! I'm here to help you plan your perfect hiking trip.")
    print("Tell me about where and when you'd like to hike!")
    print("\n(Commands: 'quit' to exit, 'reset' to start over)")
    print("-" * 60)

    agent = HikePlanningAgent()

    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() == 'quit':
                print("\n👋 Happy trails! Come back when you're ready for your next adventure!")
                break
            elif user_input.lower() == 'reset':
                agent.reset_conversation()
                print("\n🔄 Conversation reset. Let's start fresh!")
                continue
            elif not user_input:
                continue

            # Get response from agent
            print("\n🤖 Agent: ", end="")
            response = agent.generate_hiking_plan(user_input)

            # Print response in chunks to simulate streaming
            words = response.split()
            for i, word in enumerate(words):
                if i > 0 and i % 15 == 0:
                    print()
                print(word, end=" ", flush=True)
                time.sleep(0.03)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 Thanks for chatting! Stay safe on the trails!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("Let's try again!")


if __name__ == "__main__":
    main()