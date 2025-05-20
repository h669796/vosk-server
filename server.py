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
    "left",
    "right",
    "start",
    "stop", # Added a stop command, useful for paddle movement
    "exit", # Maybe?
    "[unk]" # Include "[unk]" for unknown words - Vosk needs this
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

    # Keep your overall try/except/finally structure
    try:
        async for message in websocket:
            accepted = recognizer.AcceptWaveform(message) # Store the boolean result

            if accepted:
                # --- Handle FINAL result ---
                # 'result_json' is DEFINED here
                result_json = recognizer.Result()
                # 'result_json' is USED here (after definition)
                result_dict = json.loads(result_json)
                recognized_text = result_dict.get("text", "").strip()

                if recognized_text and recognized_text != "[unk]":
                    print(f"Final Result: '{recognized_text}'")
                    await websocket.send(json.dumps({"command": recognized_text}))
                # --- End Handling FINAL result ---

            else:
                # --- Handle PARTIAL result (if no final result yet) ---
                # 'result_json' should NOT be used here
                partial_json = recognizer.PartialResult()
                partial_dict = json.loads(partial_json)
                partial_text = partial_dict.get("partial", "").strip()

                if partial_text:
                    print(f"Partial Result: '{partial_text}'")
                    # Decide what to do with partials (currently just logging)
                    pass
                # --- End Handling PARTIAL result ---

    # Exception handlers should not reference result_json unless it's guarded
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client disconnected: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Client connection error: {websocket.remote_address} - {e}")
    except Exception as e:
        # Be careful if adding logging here that uses variables from the loop
        print(f"Error handling client {websocket.remote_address}: {e}")

    # Finally block should not reference result_json
    finally:
        clients.remove(websocket)
        print(f"Cleaned up client: {websocket.remote_address}")
        # final_result = recognizer.FinalResult() # This uses a different variable

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