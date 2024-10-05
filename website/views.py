from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Memory
from . import db
import json
import utils
import requests
import boto3
import uuid
import base64
from datetime import datetime
from io import BytesIO
from sqlalchemy import extract
from dotenv import load_dotenv
import os
views = Blueprint('views', __name__)

# config = json.loads(open("config.json", "r").read())

# session = boto3.session.Session()
# s3_client = session.client(
#     's3',
#     endpoint_url=config["r2_endpoint"],
#     aws_access_key_id=config["r2_key_id"],
#     aws_secret_access_key=config["r2_key_access_key"]
# )

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
r2_endpoint = os.getenv("r2_endpoint")
r2_key_id = os.getenv("r2_key_id")
r2_key_access_key = os.getenv("r2_key_access_key")

# Initialize boto3 session and S3 client
session = boto3.session.Session()
s3_client = session.client(
    's3',
    endpoint_url=r2_endpoint,
    aws_access_key_id=r2_key_id,
    aws_secret_access_key=r2_key_access_key
)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    # if request.method == 'POST': 
    #     note = request.form.get('note')#Gets the note from the HTML 

    #     if len(note) < 1:
    #         flash('Note is too short!', category='error') 
    #     else:
    #         print("ji")

    return render_template("home.html", user=current_user)

@views.route('/api/new-memory', methods=['POST'])
def new_memory():
    data = request.json()
    base64_image = data.get('base64_image')
    locationX = data.get('locationX')
    locationY = data.get('locationY')
    voice_note = data.get('voice_note', '')
    image_data = base64.b64decode(base64_image)
    file_name = f"{uuid.uuid4()}.png"
    
    s3_client.upload_fileobj(
        BytesIO(image_data),
        "hack-the-valley-9",
        file_name,
        ExtraArgs={'ContentType': 'image/png'}
    )
    file_url = f"https://pub-5874d39fd4c54dc281a3f7d89819b0c8.r2.dev/{file_name}"

    data = {
        "model": "gpt-4o-mini",
        "messages": [
        {
          "role": "user",
          "content": [
                {"type": "text", "text": """
Given the image. Generate the following columns for the image.
                 
caption: A short description about the image.
description: A long description that is super descriptive about the image which can help the user recall what has happened.
in_danger: Yes / No. If anything in the image is potentially making the photographer in danger, return Yes. Otherwise, return No.

Return the following columns you have filled in as a dictionary. This should be the format of your response. Do not include any other text or information in your response. do not format it to appear as json markdown either.
                 """},
                {"type": "image_url", "image_url": {
                    "url": file_url
                }}
          ]
        }
    ]
    }
    api_resp = utils.cloudflare_ai_gateway("/chat/completions", data)
    resp = json.loads(api_resp["choices"][0]["message"]["content"])
    caption = resp.get("caption", "")
    description = resp.get("description", "")
    in_danger = resp.get("in_danger", "No")

    # add to database
    newMemory = Memory(caption=caption, descp=description, locationx=locationX, locationy=locationY, voice_note=voice_note, file_url=file_url)
    db.session.add(newMemory)
    db.session.commit()

    return jsonify({"caption": caption, "description": description, "in_danger": in_danger, "file_url": file_url})

@views.route("/api/search-keyword", methods=["POST"])
def search_keyword():
    keyword = request.form.get("keyword")
    memories = Memory.query.filter(Memory.caption.contains(keyword) | Memory.descp.contains(keyword)).all()
    return jsonify([memory.to_dict() for memory in memories])

@views.route("/api/search-ai", methods=["GET"])
def search_ai():
    text = request.form.get("text", "A cool student.")

    all_captions_and_timestamp = []
    memories = Memory.query.all()
    for memory in memories:
        caption = memory.caption
        timestamp = memory.timestamp
        all_captions_and_timestamp.append((memory.id, caption, timestamp))
    
    today = datetime.now().strftime("%Y-%m-%d")
    dict_captions_and_timestamp = [{"id": id, "caption": caption, "timestamp": str(timestamp)} for id, caption, timestamp in all_captions_and_timestamp]
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
        {
          "role": "user",
          "content": [
                {"type": "text", "text": f"""
Given the following dict data of ID, caption, timestamp. Find the ID of the most relevant entry to the user's query. Consider both caption and timestamp. You can do fuzzy matching if there is no exactly matching result. Today is {str(today)}.

{json.dumps(dict_captions_and_timestamp)}

Query: "{text}"

Return the following columns you have filled in as a dictionary. This should be the format of your response. Do not include any other text or information in your response. do not format it to appear as json markdown either.
                 """},
          ]
        }
    ]
    }
    api_resp = utils.cloudflare_ai_gateway("/chat/completions", data)
    resp = json.loads(api_resp["choices"][0]["message"]["content"])
    if "id" not in resp:
        return jsonify({})
    entryid = resp["id"]
    memory = Memory.query.get(entryid)
    return jsonify(memory.to_dict())

@views.route("/api/latest", methods=["GET"])
def latest():
    memories = Memory.query.order_by(Memory.timestamp.desc()).limit(1).all()
    return jsonify([memory.to_dict() for memory in memories])

@views.route("/api/summary", methods=["GET"])
def summary():
    # Get today's date
    today = datetime.now()

    # Filter memories based on the day, month, and year of today's timestamp
    memories = Memory.query.filter(
        extract('year', Memory.timestamp) == today.year,
        extract('month', Memory.timestamp) == today.month,
        extract('day', Memory.timestamp) == today.day
    ).order_by(Memory.timestamp).all()
    memories = [memory.to_dict() for memory in memories]
    # print(memories[0].keys())

    # Convert the timestamp to a string like "2024 05 10"
    # formatted_memories = []
    # for memory in memories:
    #     print(memory)
    #     # memory_dict = memory.to_dict()  # Convert memory to a dictionary
    #     memory['timestamp'] = memory["timestamp"].strftime('%Y %m %d')  # Format the timestamp
    #     formatted_memories.append(memory)
    # print(formatted_memories)

    # dict_captions_and_timestamp = [{"id": id, "descp": description, "timestamp": str(timestamp)} for id, description, timestamp in memories]
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
        {
          "role": "user",
          "content": [
                {"type": "text", "text": f"""
Given the following dict data of ID, description, timestamp. Summarize what the user has seen today. Everything they have seen are FIRST PERSON POV memories/experiences they have had today. You can combine similar events. Make the summary brief but informative and interesting. Today is {str(today)}. Their name is Baron, be personal and refer to them as "you". Below are a list of moments they have been in where they witnessed things.

{json.dumps(memories)}
                 """},
          ]
        }
    ]
    }
    api_resp = utils.cloudflare_ai_gateway("/chat/completions", data)
    resp = api_resp["choices"][0]["message"]["content"]
    
    return jsonify({"summary": resp})

@views.route("/api/getrecords", methods=["GET"])
def get_records():
    memories = Memory.query.order_by(Memory.timestamp.desc()).all()
    return jsonify([memory.to_dict() for memory in memories])

@views.route("/api/highlight", methods=["GET"])
def highlight():
    # Get today's date
    today = datetime.now()

    # Filter memories based on the day, month, and year of today's timestamp
    memories = Memory.query.filter(
        extract('year', Memory.timestamp) == today.year,
        extract('month', Memory.timestamp) == today.month,
        extract('day', Memory.timestamp) == today.day
    ).order_by(Memory.timestamp).all()
    memories = [memory.to_dict() for memory in memories]

    data = {
        "model": "gpt-4o-mini",
        "messages": [
        {
          "role": "user",
          "content": [
                {"type": "text", "text": f"""
Given the following dict data of ID, description, timestamp. Highlight what the user has seen today. Everything they have seen are FIRST PERSON POV memories/experiences they have had today. Make the highlight brief but interesting. Today is {str(today)}. Their name is Baron, be personal and refer to them as "you". Below are a list of moments they have been in where they witnessed things.

{json.dumps(memories)}
                 """},
          ]
        }
    ]
    }
    api_resp = utils.cloudflare_ai_gateway("/chat/completions", data)
    resp = api_resp["choices"][0]["message"]["content"]
    
    return jsonify({"highlight": resp})

# @views.route('/delete-note', methods=['POST'])
# def delete_note():  
#     note = json.loads(request.form) # this function expects a JSON from the INDEX.js file 
#     noteId = note['noteId']
#     note = Note.query.get(noteId)
#     if note:
#         if note.user_id == current_user.id:
#             db.session.delete(note)
#             db.session.commit()

#     return jsonify({})
