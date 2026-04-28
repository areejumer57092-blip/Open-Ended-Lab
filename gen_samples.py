import os
import wfdb
import pandas as pd
import scipy.io as sio

sample_dir = r"c:\oel\sample_data"
if not os.path.exists(sample_dir):
    os.makedirs(sample_dir)

print("Downloading real MIT-BIH ECG record via PhysioNet...")
try:
    wfdb.dl_database('mitdb', dl_dir=sample_dir, records=['100'])
    print("Files downloaded successfully.")
except Exception as e:
    print(f"Failed to download from PhysioNet: {e}")

print("Converting to CSV and MAT...")
try:
    # Load the record
    record = wfdb.rdrecord(os.path.join(sample_dir, '100'))
    
    # Take the first channel (MLII) for the first 5 minutes 
    # (fs=360, 5 min = 108000 samples). This ensures smooth dashboard rendering.
    ecg_slice = record.p_signal[:108000, 0]

    # Save as CSV
    df = pd.DataFrame({'ECG_MLII': ecg_slice})
    df.to_csv(os.path.join(sample_dir, 'real_ecg_sample.csv'), index=False)
    print("Saved real_ecg_sample.csv")

    # Save as MAT
    sio.savemat(os.path.join(sample_dir, 'real_ecg_sample.mat'), {'ecg_signal': ecg_slice})
    print("Saved real_ecg_sample.mat")

    print("Done! All formats ready.")
except Exception as e:
    print(f"Error converting formats: {e}")
