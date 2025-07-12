import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()  # Loads GOOGLE_API_KEY from .env
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

models = genai.list_models()

for model in models:
    print(f"🧠 Name: {model.name}")
    # print(f"   📌 Description: {model.description}")
    # print(f"   🧪 Generation Enabled: {model.supports_generation}")
    print("--------------------------------------------------")
