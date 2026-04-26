from openrouter import OpenRouter
import os
import dotenv

dotenv.load_dotenv()

def main():
    print("Hello from journalist-helper!")
    # call_model coming soon! For now, use chat.send with tools:


    with OpenRouter(
        api_key=os.getenv("OPENROUTER_API_KEY")
    ) as client:
        response = client.chat.send(
            model="z-ai/glm-4.5-air:free",
            messages=[
                {"role": "user", "content": "What is the weather in San Francisco?"}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"]
                    }
                }
            }]
        )

    print(response.choices[0].message)


if __name__ == "__main__":
    main()
