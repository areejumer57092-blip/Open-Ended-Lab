import numpy as np
import pandas as pd
import scipy.io as sio
import os
import sys

sample_dir = r"c:\oel\sample_data"
if not os.path.exists(sample_dir):
    os.makedirs(sample_dir)

fs = 250
minutes = 15 # Massive 15 minute dataset to show intense variations
seconds = minutes * 60
length = fs * seconds
time = np.linspace(0, seconds, length)

# Create a highly dynamic heart rate that wanders elegantly between 60 and 150 BPM over time
hr_base = 90 + 40 * np.sin(2 * np.pi * time / 450) + 15 * np.sin(2 * np.pi * time / 150)
hr_base = np.clip(hr_base, 50, 160)

# Create dynamic Respiratory Sinus Arrhythmia (HF component)
# It will wax and wane inversely to HR to create distinct chart crossings
rsa_strength = 0.12 + 0.08 * np.cos(2 * np.pi * time / 300)
rsa = rsa_strength * np.sin(2 * np.pi * 0.25 * time) # 0.25Hz respiration

data = np.zeros(length)
current_phase = 0

print("Synthesizing 15 minutes of extreme HRV raw waveform...")

# Fast loop generation
for i in range(length):
    t = time[i]
    bw = np.sin(2 * np.pi * 0.05 * t) * 0.05
    
    interval = (60 / hr_base[i]) + rsa[i]
    interval_samples = int(interval * fs)
    
    val = bw
    if 20 < current_phase < 40:
        val += 0.15 * np.sin(np.pi * (current_phase - 20) / 20)
    elif 60 < current_phase < 70:
        val -= 0.2
    elif 70 <= current_phase < 80:
        val += 1.5
    elif 80 <= current_phase < 90:
        val -= 0.4
    elif 120 < current_phase < 170:
        val += 0.3 * np.sin(np.pi * (current_phase - 120) / 50)
        
    val += np.random.normal(0, 0.01) # Baseline noise
    data[i] = val
    
    current_phase += 1
    if current_phase >= interval_samples:
        current_phase = 0

print("Saving directly to export directory...")
sio.savemat(os.path.join(sample_dir, 'synthetic_extreme_hrv.mat'), {'ecg_signal': data})
print("Success! Extreme HRV target acquired.")
