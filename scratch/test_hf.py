import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
model_id = os.getenv("HUGGINGFACE_MODEL_ID")

print(f"HF API Key: {api_key[:10]}...")
print(f"HF Model ID: {model_id}")

url = f"https://api-inference.huggingface.co/models/{model_id}"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "inputs": "<|start_header_id|>user<|end_header_id|>\n\nHello!<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
    "parameters": {
        "max_new_tokens": 100,
        "temperature": 0.7
    }
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error calling Hugging Face:", e)
