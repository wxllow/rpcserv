# Intermediary web server for taking HTTP requests and forwarding them to the connnected socket.io clients

import os
from flask import Flask, jsonify, request, redirect
from flask_socketio import SocketIO, join_room
from pymongo import MongoClient
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import secrets
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["RPCSERV_FLASK_SECRET"]
socketio = SocketIO(app, cors_allowed_origins="*")

DB_URL = os.environ.get("RPCSERV_DB_URL", "mongodb://localhost:27017")
CLIENT_ID = os.environ["RPCSERV_CLIENT_ID"]
CLIENT_SECRET = os.environ["RPCSERV_CLIENT_SECRET"]
CALLBACK_URI = os.environ["RPCSERV_CALLBACK_URI"]
DISCORD_OAUTH2_URL = (
    "https://discord.com/api/oauth2/authorize"
    f"?client_id={quote(CLIENT_ID)}"
    f"&redirect_uri={quote(CALLBACK_URI)}"
    "&response_type=code"
    "&scope=identify"
)

db = MongoClient()["discord"]
users = db["users"]
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2 per second"],
    storage_uri=DB_URL,
)

# Make discord_access_token and secret be indexed in the database for faster lookup
users.create_index("discord_access_token")
users.create_index("secret")


@app.after_request
def after_request(response):
    # CORS
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")

    return response


# Reset the user's secret
@app.route("/authorize/reset")
def reset():
    return redirect(DISCORD_OAUTH2_URL + "&state=reset")


@app.route("/")
@app.route("/authorize")
def authorize():
    return redirect(DISCORD_OAUTH2_URL)


# URL for authorizing Discord callback
@app.route("/authorize/callback")
def authorize_callback():
    # Get the code from the URL
    code = request.args.get("code")
    state = request.args.get("state")

    # Send a POST request to Discord to get the access token
    response = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": CALLBACK_URI,
            "scope": "identify",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        return jsonify({"error": "Authentication error"}), 400

    # Get the access token from the response
    discord_access_token = response.json()["access_token"]

    # Get user's Discord ID
    discord_id_resp = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {discord_access_token}"},
    )

    if discord_id_resp.status_code != 200:
        return jsonify({"error": "Authentication error"}), 400

    discord_id = discord_id_resp.json()["id"]

    # Check if the user is already in the database
    user = users.find_one({"_id": discord_id})

    if user:
        # Update the user's access token
        users.update_one(
            {"_id": discord_id},
            {"$set": {"discord_access_token": discord_access_token}},
        )

        if state == "reset":
            # Reset the user's secret
            secret = secrets.token_urlsafe(32)
            users.update_one({"_id": discord_id}, {"$set": {"secret": secret}})
            return jsonify({"secret": secret})

        return jsonify({"secret": user["secret"]})

    # Create a unique access token for this user to use to interact with the socket.io server
    secret = secrets.token_urlsafe(32)

    # Save user to the database
    users.insert_one(
        {
            "_id": discord_id,
            "discord_access_token": discord_access_token,
            "secret": secret,
        }
    )

    return jsonify({"secret": secret})


@app.route("/status/update", methods=["POST"])
def status_update():
    # Get JSON body
    data = request.get_json()

    print(data)

    if not data:
        return jsonify({"error": "No body"}), 400

    secret = data.get("secret")
    clear = data.get("clear")
    details = data.get("details")
    state = data.get("state")
    metadata = data.get("metadata")

    if not secret or not (clear or (details and state)):
        print("ERROR: Missing body parameters")
        return jsonify({"error": "Missing body parameters"}), 400

    secret = secret.strip()

    # Get user from database
    user = users.find_one({"secret": secret})

    if not user:
        print(f"ERROR: Invalid secret: {secret}")
        return jsonify({"error": "Invalid secret"}), 400

    if clear:
        # Send `status_clear` event to socke
        socketio.emit("status_clear", room=user["_id"])
        return "", 204

    # Send `status_update` event to socket.io clients in room `user._id`
    socketio.emit(
        "status_update",
        {
            "details": details,
            "state": state,
            "service": data.get("service"),
            "metadata": metadata,
        },
        room=user["_id"],
    )

    print("Sent status update")
    # Return success
    return "", 204


# Connect to socket.io
@socketio.on("connect", namespace="/")
def connect():
    # Get the user's secret from the query string
    secret = request.args.get("secret")

    if not secret:
        return False

    # Get the user from the database
    user = users.find_one({"secret": secret})

    if not user:
        return False

    # Add user to a room with the user's Discord ID
    join_room(user["_id"])

    # Return success
    return True


if __name__ == "__main__":
    socketio.run(
        app,
        host=os.environ.get("RPCSERV_HOST", "0.0.0.0"),
        port=os.environ.get("RPCSERV_PORT", "8237"),
        debug=os.environ.get("RPCSERV_DEBUG", "true").lower() == "true",
    )
