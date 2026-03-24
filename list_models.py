from google import genai
import os

# Get API key from .env or environment
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("ERROR: GOOGLE_API_KEY not set")
    exit(1)

client = genai.Client(api_key=api_key)

# Test generate_content with different models
models_to_test = [
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-flash-latest',
    'gemini-pro-latest'
]

for model_name in models_to_test:
    print(f"\nTesting generate_content with {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=["Hello, can you say 'test successful'?"]
        )
        if response.text:
            print(f"  SUCCESS: {response.text[:100]}")
        else:
            print(f"  NO TEXT RESPONSE")
    except Exception as e:
        print(f"  FAILED: {e}")
