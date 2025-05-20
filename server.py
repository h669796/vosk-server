import asyncio
import websockets
import json
import vosk
import sys
import os

MODEL_PATH = "model-en" 
VOSK_SAMPLE_RATE = 16000 
SERVER_HOST = "localhost" 
SERVER_PORT = 8765        

COMMANDS = json.dumps([
    "left",
    "right",
    "start",
    "stop", 
    "exit", 
    "[unk]" 
])

if not os.path.exists(MODEL_PATH):
    print(f"Model path '{MODEL_PATH}' not found. Please download/extract the model.")
    sys.exit(1)

vosk.SetLogLevel(-1) 
model = vosk.Model(MODEL_PATH)

recognizer = vosk.KaldiRecognizer(model, VOSK_SAMPLE_RATE, COMMANDS)
recognizer.SetWords(True) 

print(f"Vosk model loaded. Grammar: {COMMANDS}")

clients = set()

async def handle_client(websocket):
    """Handles a single client connection."""
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            accepted = recognizer.AcceptWaveform(message) 

            if accepted:
                
                
                result_json = recognizer.Result()
                
                result_dict = json.loads(result_json)
                recognized_text = result_dict.get("text", "").strip()

                if recognized_text and recognized_text != "[unk]":
                    print(f"Final Result: '{recognized_text}'")
                    await websocket.send(json.dumps({"command": recognized_text}))
            
            else:
                
                partial_json = recognizer.PartialResult()
                partial_dict = json.loads(partial_json)
                partial_text = partial_dict.get("partial", "").strip()

                if partial_text:
                    print(f"Partial Result: '{partial_text}'")
                    
                    pass
                
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client disconnected: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Client connection error: {websocket.remote_address} - {e}")
    except Exception as e:
        
        print(f"Error handling client {websocket.remote_address}: {e}")

    finally:
        clients.remove(websocket)
        print(f"Cleaned up client: {websocket.remote_address}")
        
async def start_server():
    """Starts the WebSocket server."""
    async with websockets.serve(handle_client, SERVER_HOST, SERVER_PORT):
        print(f"WebSocket server started on ws://{SERVER_HOST}:{SERVER_PORT}")
        await asyncio.Future() 

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nServer stopped.")