import asyncio
import websockets
import json
import vosk
import sys
import os

# --- Configuration ---
MODEL_PATH = "model-en" # Path to your downloaded Vosk model folder
VOSK_SAMPLE_RATE = 16000 # Vosk typically uses 16kHz or 8kHz
SERVER_HOST = "localhost" # Or "0.0.0.0" to listen on all network interfaces
SERVER_PORT = 8765        # Port for the WebSocket server

# Define your expected commands for better accuracy
# Format for Vosk grammar: JSON list of strings
# Make sure words are in the model's dictionary (check model/graph/words.txt if needed)
COMMANDS = json.dumps([
    # Categories (use English equivalents, keep lowercase)
    "general knowledge",    # Maps to "Generell Kunnskap" in JS
    "history",              # Add English names for your other categories
    "geography",
    "science",
    "random question",      # Maps to "Tilfeldig spørsmål" in JS

    # Difficulties (English, lowercase)
    "easy",                 # Maps to "lett" in JS
    "medium",               # Maps to "middels" in JS
    "hard",                 # Maps to "vanskelig" in JS

    # Answers (lowercase letters - language neutral)
    "a",
    "b",
    "c",
    "d",

    # Optional Navigation/Control (English)
    "start",
    "stop", # Usually handled by button, but can include
    "home", # Maps to returnToHome()

    # IMPORTANT - Keep for Vosk
    "[unk]"
])

# --- Vosk Setup ---
if not os.path.exists(MODEL_PATH):
    print(f"Model path '{MODEL_PATH}' not found. Please download/extract the model.")
    sys.exit(1)

vosk.SetLogLevel(-1) # Suppress excessive Vosk logging
model = vosk.Model(MODEL_PATH)
# Use the grammar list when creating the recognizer
recognizer = vosk.KaldiRecognizer(model, VOSK_SAMPLE_RATE, COMMANDS)
recognizer.SetWords(True) # Optional: Get word-level details if needed

print(f"Vosk model loaded. Grammar: {COMMANDS}")

# --- WebSocket Handling ---
clients = set()

async def handle_client(websocket):
    """Handles a single client connection."""
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    # Create a fresh recognizer for each connection if needed, or reuse
    # Reusing might be okay if only one client expected at a time
    # For multiple simultaneous clients, create recognizer here:
    # rec = vosk.KaldiRecognizer(model, VOSK_SAMPLE_RATE, COMMANDS)

    try:
        async for message in websocket:
            # Assume message is binary audio data (raw PCM)
            if recognizer.AcceptWaveform(message):
                result_json = recognizer.Result()
                result_dict = json.loads(result_json)
                recognized_text = result_dict.get("text", "").strip()

                # Check if the recognized text is one of our commands (excluding "[unk]")
                if recognized_text and recognized_text != "[unk]":
                    print(f"Recognized: '{recognized_text}'")
                    # Send the recognized command back to the client
                    await websocket.send(json.dumps({"command": recognized_text}))
                # else:
                    # Optionally handle partial results if needed
                    # partial_json = recognizer.PartialResult()
                    # print(f"Partial: {partial_json}")

            # else: # Handle partial results if you want intermediate feedback
            #     partial_json = recognizer.PartialResult()
            #     partial_dict = json.loads(partial_json)
            #     partial_text = partial_dict.get("partial", "").strip()
            #     if partial_text:
            #          print(f"Partial: '{partial_text}'")
            #          # Maybe send partial results back too?
            #          # await websocket.send(json.dumps({"partial": partial_text}))


    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client disconnected: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Client connection error: {websocket.remote_address} - {e}")
    except Exception as e:
        print(f"Error handling client {websocket.remote_address}: {e}")
    finally:
        clients.remove(websocket)
        print(f"Cleaned up client: {websocket.remote_address}")
        # If recognizer was created per-client, clean it up here.

# --- Start Server ---
async def start_server():
    """Starts the WebSocket server."""
    async with websockets.serve(handle_client, SERVER_HOST, SERVER_PORT):
        print(f"WebSocket server started on ws://{SERVER_HOST}:{SERVER_PORT}")
        await asyncio.Future() # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nServer stopped.")