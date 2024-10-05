from dotenv import load_dotenv
import requests
import json
import os

# config = json.load(open('config.json', 'r'))

# def cloudflare_ai_gateway(path, data):
#     r = requests.post(f'https://gateway.ai.cloudflare.com/v1/5c839b3a3bb73452ccfdd5a830f2844b/htv09/openai{path}', json=data, headers={'Authorization': f'Bearer {config["openai_key"]}', 'Content-Type': 'application/json'})
#     return r.json()

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
openai_key = os.getenv("openai_key")
cloudflare_base_url = "https://gateway.ai.cloudflare.com/v1/5c839b3a3bb73452ccfdd5a830f2844b/htv09/openai"

# Function to make request to Cloudflare AI gateway
def cloudflare_ai_gateway(path, data):
    r = requests.post(
        f'{cloudflare_base_url}{path}',
        json=data,
        headers={
            'Authorization': f'Bearer {openai_key}',
            'Content-Type': 'application/json'
        }
    )
    
    if r.headers.get('Content-Type') == 'application/json':
        return r.json()
    else:
        return r.content
