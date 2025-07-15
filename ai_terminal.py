import subprocess
import sys
import os
import requests
import json

class WindowsAIAssistant:
    def __init__(self, model_name="llama3.2:3b", ollama_url="http://localhost:11434"):
        """Initialize the AI assistant with Ollama."""
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.api_url = f"{ollama_url}/api/generate"
        self.system_prompt = """
        You are a Windows command line assistant. Your job is to:
        1. Interpret user requests and generate appropriate Windows commands
        2. Always respond in JSON format with this structure:
        {
            "command": "the actual command to execute",
            "explanation": "brief explanation of what this command does",
            "safe": true/false (whether the command is safe to auto-execute)
        }
        
        Guidelines:
        - Use PowerShell or CMD commands as appropriate
        - Mark commands as "safe": false if they could modify system files, install software, or cause damage
        - For file operations, use full paths when possible
        - Always explain what the command does
        
        Examples:
        User: "show me disk usage"
        Response: {"command": "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace", "explanation": "Shows disk usage for all drives", "safe": true}
        
        User: "list running processes"
        Response: {"command": "tasklist", "explanation": "Lists all currently running processes", "safe": true}
        """
    
    def get_ai_response(self, user_input):
        """Get AI response for user input using Ollama."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": f"{self.system_prompt}\n\nUser: {user_input}\nResponse:",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 300
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.json()["response"].strip()
                
                # Try to parse JSON response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass
                    
                    return {
                        "command": None,
                        "explanation": f"Error parsing AI response: {content}",
                        "safe": False
                    }
            else:
                return {
                    "command": None,
                    "explanation": f"Error: Ollama server returned status {response.status_code}",
                    "safe": False
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "command": None,
                "explanation": "Error: Cannot connect to Ollama server. Make sure Ollama is running.",
                "safe": False
            }
        except Exception as e:
            return {
                "command": None,
                "explanation": f"Error getting AI response: {str(e)}",
                "safe": False
            }
    
    def execute_command(self, command, use_powershell=True):
        """Execute a command safely."""
        try:
            if use_powershell:
                # Use PowerShell
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # Use CMD
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_ollama_connection(self):
        """Check if Ollama server is running and model is available."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.model_name not in model_names:
                    print(f"⚠️  Model '{self.model_name}' not found.")
                    print("Available models:", model_names)
                    print(f"To install the model, run: ollama pull {self.model_name}")
                    return False
                return True
            else:
                print("❌ Ollama server is not responding properly")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Ollama server")
            print("Make sure Ollama is installed and running:")
            print("1. Download from: https://ollama.com/")
            print("2. Run: ollama serve")
            return False
        except Exception as e:
            print(f"❌ Error checking Ollama: {str(e)}")
            return False
    
    def run_interactive(self):
        """Run the interactive assistant."""
        print("=== Windows AI Command Assistant ===")
        print("Type 'quit' to exit")
        print("Type 'help' for usage information")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'models':
                    try:
                        response = requests.get(f"{self.ollama_url}/api/tags")
                        if response.status_code == 200:
                            models = response.json().get("models", [])
                            print("\nAvailable models:")
                            for model in models:
                                print(f"  - {model['name']}")
                                print(f"    Size: {model.get('size', 'Unknown')}")
                        else:
                            print("❌ Could not fetch models")
                    except Exception as e:
                        print(f"❌ Error fetching models: {str(e)}")
                    print()
                    continue
                
                if user_input.lower() == 'help':
                    print("\nUsage:")
                    print("- Ask for any Windows command in natural language")
                    print("- Example: 'show me running processes'")
                    print("- Example: 'list files in current directory'")
                    print("- Example: 'check network connections'")
                    print("- The AI will suggest a command and ask for confirmation")
                    print()
                    continue
                
                if not user_input:
                    continue
                
                print("\nThinking...")
                
                # Get AI response
                ai_response = self.get_ai_response(user_input)
                
                if not ai_response.get("command"):
                    print(f"❌ {ai_response.get('explanation', 'No command generated')}")
                    continue
                
                # Show the suggested command
                print(f"\n📝 Suggested command: {ai_response['command']}")
                print(f"💡 Explanation: {ai_response['explanation']}")
                
                # Safety check
                if not ai_response.get("safe", False):
                    print("⚠️  WARNING: This command might modify your system!")
                
                # Ask for confirmation
                confirm = input("\n🔄 Execute this command? (y/n): ").lower()
                
                if confirm == 'y':
                    print("\n🔄 Executing...")
                    
                    # Execute the command
                    result = self.execute_command(ai_response['command'])
                    
                    if result.get("success"):
                        if result["stdout"]:
                            print("✅ Output:")
                            print(result["stdout"])
                        if result["stderr"]:
                            print("⚠️  Errors:")
                            print(result["stderr"])
                    else:
                        print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
                else:
                    print("❌ Command cancelled")
                
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

def main():
    """Main function to run the assistant."""
    # Default model - you can change this
    model_name = "llama3.2:3b"  # Change this to your preferred model
    
    # You can also specify a different model via command line
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
        print(f"Using model: {model_name}")
    
    assistant = WindowsAIAssistant(model_name)
    assistant.run_interactive()

if __name__ == "__main__":
    main()