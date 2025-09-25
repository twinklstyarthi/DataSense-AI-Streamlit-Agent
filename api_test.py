import os
import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core import exceptions

def test_api_key():
    """
    Loads the API key from .env and makes a single test call to the Gemini API.
    """
    print("--- Starting API Key Test ---")
    
    try:
        # 1. Load the API key from the .env file
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            print("❌ ERROR: GOOGLE_API_KEY not found in .env file.")
            return

        print("✅ API Key loaded successfully.")

        # 2. Configure the SDK
        genai.configure(api_key=api_key)
        print("✅ Google AI SDK configured.")

        # 3. Create a model and send a prompt
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Model created. Sending a test prompt...")
        
        response = model.generate_content("What is the capital of India?")

        print("\n--- API Response ---")
        print(response.text)
        print("--------------------")
        
        print("\n🎉 SUCCESS! Your API key and connection are working.")

    except exceptions.ResourceExhausted as e:
        print("\n--- TEST FAILED ---")
        print("❌ ERROR: You are still over the free tier quota.")
        print("The API key is likely correct, but you need to wait for the daily limit to reset.")
        
    except Exception as e:
        print("\n--- TEST FAILED ---")
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_api_key()