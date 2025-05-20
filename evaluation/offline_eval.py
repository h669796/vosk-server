# offline_eval.py  — baseline sweep without RNNoise
import json, os, glob, csv, collections, math
from pathlib import Path
from datetime import datetime

from pydub import AudioSegment
import vosk

# ------------------------------------------------------------------
# Paths
ROOT       = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "model-en"
VOICE_DIR  = ROOT / "evaluation" / "clean_commands"
NOISE_WAV  = ROOT / "evaluation" / "mri_noise.wav"

timestamp  = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
OUT_CSV    = ROOT / "evaluation" / f"eval_{timestamp}.csv"

# ------------------------------------------------------------------
COMMANDS_JSON = '[ "general knowledge", "history", "geography", "science", "random question", "easy", "medium", "hard", "a", "b", "c", "d", "[unk]" ]'
SNR_STEPS     = [20, 15, 10, 5]
N_DUP         = 1               # ≈110 utterances

def mix(clean: AudioSegment, noise: AudioSegment, snr_db: float):
    if len(noise) < len(clean):
        noise = (noise * (len(clean)//len(noise)+1))[:len(clean)]
    gain = clean.rms / (10**(snr_db/20) * noise.rms + 1e-9)
    return clean.overlay(noise.apply_gain(20 * math.log10(gain)))

# ------------------------------------------------------------------
vosk.SetLogLevel(-1)
model = vosk.Model(str(MODEL_PATH))
rec   = vosk.KaldiRecognizer(model, 16000, COMMANDS_JSON)

noise_clip = AudioSegment.from_file(NOISE_WAV)
wav_files  = glob.glob(str(VOICE_DIR / "*.wav")) * N_DUP

results = []

for snr in SNR_STEPS:
    correct = total = 0
    for wav in wav_files:
        clean  = AudioSegment.from_file(wav)
        noisy  = mix(clean, noise_clip, snr)
        rec.AcceptWaveform(noisy.raw_data)
        pred = json.loads(rec.Result())["text"].strip() or "[unk]"
        if pred == Path(wav).stem.replace('_', ' '):
            correct += 1
        total += 1
        rec.Reset()
    acc = round(100 * correct / total, 1)
    print(f"SNR {snr:>2} dB → {correct}/{total}  ({acc} %)")
    results.append((snr, correct, total, acc))

# ------------------------------------------------------------------
with OUT_CSV.open("w", newline="") as f:
    csv.writer(f).writerows([("SNR_dB","correct","total","accuracy_pct"), *results])

print(f"\nSaved results to {OUT_CSV}")

