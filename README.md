# Vosk WebSocket Server

This repository contains Python-based WebSocket servers that use the Vosk Speech Recognition Toolkit to provide speech-to-text services for client applications. It includes a specific server tailored for a Voice Quiz game (`quiz_server.py`). It also includes scripts for evaluating speech recognition accuracy (`offline_eval.py`).

## Features

* **WebSocket Interface:** Provides a WebSocket endpoint for real-time audio streaming and text transcription.
* **Vosk Integration:** Utilizes the Vosk Speech Recognition Toolkit for robust speech-to-text.
* **Customizable Grammar:** Allows for defining specific command lists for more accurate recognition in targeted applications.
* **Two Server Implementations:**
    * `quiz_server.py`: Specifically configured for the Voice Quiz application, recognizing categories, difficulty levels, and answers.
    * `server.py`: A general server with a different set of commands like "left", "right", "start", "stop", "exit".
* **Offline Evaluation:** Includes `offline_eval.py` to test the accuracy of the Vosk model with varying levels of background noise (Signal-to-Noise Ratio - SNR).

## Core Components

### 1. `quiz_server.py`

This server is designed to work as the backend for the Voice Quiz game.
* It listens for audio data on a WebSocket connection (default: `ws://localhost:8765`).
* It uses a specific Vosk grammar tailored for quiz commands, including:
    * **Categories:** "general knowledge", "history", "geography", "science", "random question"
    * **Difficulties:** "easy", "medium", "hard"
    * **Answers:** "a", "b", "c", "d"
    * **Navigation/Control:** "start", "stop", "home"
* Recognized commands are sent back to the connected client (the Voice Quiz frontend) as JSON messages.
* Requires the Vosk English model (`model-en`).

### 2. `server.py`

This is a more generic Vosk WebSocket server.
* It also listens for audio data on `ws://localhost:8765`.
* It uses a different set of commands: "left", "right", "start", "stop", "exit".
* It can provide both partial and final recognition results.
* Recognized commands are sent back as JSON messages.
* Requires the Vosk English model (`model-en`).

### 3. `offline_eval.py`

This script is used for evaluating the speech recognition performance of the Vosk model.
* It takes clean audio command files, mixes them with noise (e.g., `mri_noise.wav`) at different Signal-to-Noise Ratios (SNRs: 20, 15, 10, 5 dB).
* It then feeds the noisy audio to the Vosk recognizer (using the same command list as `quiz_server.py`).
* The script calculates and prints the accuracy (percentage of correctly recognized commands) for each SNR level.
* Results are saved to a CSV file in the `evaluation/` directory (e.g., `eval_YYYY-MM-DDTHH-MM-SS.csv`). The CSV files like `eval_2025-04-29T15-22-34.csv`, `eval_2025-04-30T15-24-01.csv`, `eval_2025-05-05T18-07-06.csv`, `eval_2025-05-05T22-18-27.csv`, and `eval_results.csv` store these evaluation results, typically containing columns for SNR_dB, correct, total, and accuracy_pct.

## Project Structure 
├── model-en/                 # Directory for the Vosk English model
├── evaluation/
│   ├── clean_commands/       # Directory for clean audio files for evaluation
│   ├── mri_noise.wav         # Example noise file for evaluation
│   ├── offline_eval.py       # Evaluation script
│   └── *.csv                 # Evaluation results
├── quiz_server.py            # WebSocket server for the Quiz Game
├── server.py                 # General purpose WebSocket server
└── README.md                 # This file

## Prerequisites

1.  **Python 3.x**
2.  **Vosk:** `pip install vosk`
3.  **Websockets:** `pip install websockets`
4.  **Pydub (for `offline_eval.py`):** `pip install pydub`
5.  **Vosk English Model (`model-en`):**
    * Download a Vosk English model (e.g., `vosk-model-en-us-0.15` or a smaller one).
    * Extract and rename the model folder to `model-en` and place it in the root of this `vosk-server` project.

## Setup and Running

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/h669796/vosk-server](https://github.com/h669796/vosk-server)
    cd vosk-server
    ```

2.  **Install Dependencies:**
    ```bash
    pip install vosk websockets pydub
    ```

3.  **Download and Place Vosk Model:**
    * Download the model-en-us-0.15 English model from the [Vosk Models Page](https://alphacephei.com/vosk/models).
    * Extract the archive.
    * Rename the extracted folder to `model-en` and place it in the root of the `vosk-server` directory.

4.  **Running the Servers:**

    * **For the Voice Quiz (`quiz_server.py`):**
        ```bash
        python quiz_server.py
        ```
        The server will start and listen on `ws://localhost:8765`.

5.  **Running Offline Evaluation (`offline_eval.py`):**
    * Ensure you have clean `.wav` command files in the `evaluation/clean_commands/` directory.
    * Ensure `evaluation/mri_noise.wav` (or your chosen noise file) exists.
    * Modify paths in `offline_eval.py` if your structure differs.
    * Run the script:
        ```bash
        python evaluation/offline_eval.py
        ```
        Results will be printed to the console and saved in a new CSV file in the `evaluation/` directory.

## Usage with Client Applications

These servers are designed to be used by WebSocket client applications that stream audio data and receive text transcriptions.

* **Endpoint:** Clients should connect to `ws://localhost:8765`.
* **Audio Format:** The server expects audio data, typically 16kHz PCM
* **Communication:**
    * The client sends raw audio binary messages.
    * The server sends JSON messages back, usually containing a `{"command": "recognized_text"}` structure for `quiz_server.py` 

## Troubleshooting

* **Server not starting:**
    * Ensure all Python dependencies (Vosk, websockets) are installed.
    * Verify the Vosk model (`model-en`) is correctly downloaded, extracted, named, and placed in the project's root directory. The server scripts will exit if the model path is not found.
* **Poor recognition accuracy:**
    * Ensure clear audio input and minimal background noise for client applications.
    * The defined grammar in `quiz_server.py` and `server.py` is crucial. Phrases outside this grammar are less likely to be recognized correctly.
* **Connection issues:**
    * Check that no other application is using port `8765`.
    * Ensure your client application is attempting to connect to the correct WebSocket address (`ws://localhost:8765`).
    * Check the server console output for any error messages.
