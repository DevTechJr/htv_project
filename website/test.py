import requests

if __name__ == "__main__":
    r = requests.get("http://localhost:5000/api/new-memory", data={"base64_image": "", "locationX": 43.7867324, "locationY": -79.1908556, "voice_note": "This is Alex"})