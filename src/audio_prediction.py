import pyaudio
import numpy as np
import torch
import torchaudio
import pandas as pd
import io
import requests

# Import the PyTorch port of YAMNet
from torch_vggish_yamnet import yamnet

def load_class_names():
    # (Same as before)
    url = "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"
    try:
        s = requests.get(url).content
        class_map = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return class_map['display_name'].tolist()
    except Exception as e:
        print("Error downloading class map.")
        exit()

def main():
    print("Loading YAMNet model...")
    model = yamnet.yamnet(pretrained=True)
    model.eval()

    class_names = load_class_names()
    print('Class names: ', class_names)
    print(len(class_names))
    baby_cry_index = class_names.index("Baby cry, infant cry")

    # --- VITAL: Define the Spectrogram Transformer ---
    # YAMNet requires very specific settings:
    # 16kHz SR, Window 25ms, Hop 10ms, 64 Mel Bands, 125-7500Hz
    mel_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=16000,
        n_fft=512,
        win_length=400,    # 25ms * 16000
        hop_length=160,    # 10ms * 16000
        f_min=125,
        f_max=7500,
        n_mels=64
    )

    # PyAudio Setup
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    # We need exactly 15600 samples for 0.975s
    CHUNK = 15600 
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                        input=True, frames_per_buffer=CHUNK)

    print("\n🎤 Listening... (Press Ctrl+C to stop)")
    
    try:
        while True:
            # 1. Read raw bytes
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # 2. Convert to float tensor [-1, 1]
            numpy_data = np.frombuffer(data, dtype=np.int16)
            waveform = torch.tensor(numpy_data, dtype=torch.float32) / 32768.0

            # 3. --- FIX: Convert Waveform to Spectrogram ---
            # Shape becomes: [64, 98] (Mel_Bands, Frames)
            spec = mel_transform(waveform) 
            
            # 4. Apply Log (YAMNet expects Log-Mel)
            # We add a small epsilon (0.001) to avoid log(0)
            log_spec = torch.log(spec + 0.001)

            # 5. Reshape for the Model
            # YAMNet expects: [Batch, 1, Frames, Mel_Bands]
            # Currently we have [Mel_Bands, Frames]. 
            # We need to transpose to [Frames, Mel_Bands] -> [98, 64]
            log_spec = log_spec.transpose(0, 1)
            
            # We slice to exactly 96 frames (YAMNet specific input size)
            # Sometimes the math results in 97 or 98 frames, we trim to 96.
            log_spec = log_spec[:96, :] 

            # Add Batch and Channel dimensions: [1, 1, 96, 64]
            model_input = log_spec.unsqueeze(0).unsqueeze(0)

            # --- Inference ---
            with torch.no_grad():
                _, prediction = model(model_input)
                
            prediction = prediction.squeeze()
            softmax_prediction = torch.softmax(prediction, dim=0)
            max_index = torch.argmax(softmax_prediction)
            max_prob = softmax_prediction[max_index].item()
            max_name = class_names[max_index]
            print(f"Max probability: {max_prob:.2f} for {max_name}")
            if softmax_prediction[baby_cry_index].item() > 0.3:
                print(f"\033[91m👶 BABY CRYING! {softmax_prediction[baby_cry_index].item():.2f}\033[0m")
            else:
                print(f"{softmax_prediction[baby_cry_index].item():.2f}", end='\r')

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()