import os
import wfdb
import pandas as pd
import scipy.io as sio

sample_dir = r"c:\oel\sample_data"
if not os.path.exists(sample_dir):
    os.makedirs(sample_dir)

print("Downloading Record 119 (Famous for Ventricular Ectopics)...")
try:
    # Record 119 contains intense Premature Ventricular Contractions (Bigeminy)
    wfdb.dl_database('mitdb', dl_dir=sample_dir, records=['119'])
    
    # Load the record
    record = wfdb.rdrecord(os.path.join(sample_dir, '119'))
    
    # Slice the first 5 minutes. Record 119 exhibits PVCs almost immediately
    ecg_slice = record.p_signal[:108000, 0]

    # Save as CSV
    df = pd.DataFrame({'ECG': ecg_slice})
    df.to_csv(os.path.join(sample_dir, 'ectopic_sample_119.csv'), index=False)

    # Save as MAT
    sio.savemat(os.path.join(sample_dir, 'ectopic_sample_119.mat'), {'ecg_signal': ecg_slice})

    print("Done! ectopic_sample_119 files are ready.")
except Exception as e:
    print(f"Error: {e}")
