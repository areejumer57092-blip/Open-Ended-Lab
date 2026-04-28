ECG and HRV Analysis Dashboard

lab Overview

This is an ECG-based Heart Rate Variability (HRV) analysis dashboard developed using Python as part of a Biomedical Signal Processing lab. The system processes ECG signals, extracts RR intervals, and performs HRV analysis using time-domain, non-linear, and frequency-domain methods.

The main purpose of this lab is to study heart rate variability and observe how the autonomic nervous system affects heartbeat dynamics.

Objectives
- Extract RR intervals from ECG signals using R-peak detection  
- Perform time-domain HRV analysis  
- Compute statistical HRV parameters such as SDNN and RMSSD  
- Perform non-linear HRV analysis using Poincaré plot and entropy measures  
- Perform frequency-domain analysis using Power Spectral Density (PSD)  
- Implement segmented HRV analysis to observe changes over time  
- Build a Python-based dashboard for visualization of results  

 Features

 ECG Processing
- ECG signal input and preprocessing  
- R-peak detection from ECG waveform  
- RR interval extraction  

Time-Domain HRV Analysis
- SDNN calculation  
- RMSSD calculation  
- Basic statistical analysis of RR intervals  

Non-Linear Analysis
- Poincaré plot (RR(n) vs RR(n+1))  
- SD1 and SD2 computation  
- Entropy-based measure for signal complexity  

Frequency-Domain Analysis
- Power Spectral Density (PSD) computation using Python  
- LF and HF band analysis  
- LF/HF ratio calculation for autonomic balance  

Segmented HRV Analysis
- RR intervals divided into time windows   
- Observation of HRV changes over time  

Methodology
1. ECG signal is loaded and preprocessed in Python  
2. R-peaks are detected from the ECG signal  
3. RR intervals are calculated from detected peaks  
4. HRV features are extracted using different analysis methods  
5. Signal is divided into segments for time-varying analysis  
6. Results are visualized in a dashboard  

Results Overview
The dashboard generates the following outputs:
- ECG waveform with detected R-peaks  
- RR interval trend plot  
- Time-domain HRV values (SDNN, RMSSD)  
- Poincaré plot showing variability pattern  
- Entropy-based complexity measure  
- PSD plot showing LF and HF distribution  
- Segment-wise HRV variation plots  

 Physiological Significance
- LF component reflects combined sympathetic and parasympathetic activity  
- HF component reflects parasympathetic (vagal) activity  
- LF/HF ratio shows balance between stress and relaxation responses  
- HRV measures help understand autonomic nervous system regulation  

Tools Used
- Python  
- Libraries used for signal processing and visualization (e.g., NumPy, SciPy, Matplotlib)  
- ECG signal processing techniques  
- HRV analysis methods  

Conclusion
This lab successfully implements an ECG and HRV analysis system using Python. It combines time-domain, non-linear, and frequency-domain approaches to analyze heart rate variability and provides visual insight into autonomic nervous system behavior.

Future Improvements
- Real-time ECG signal processing  
- Integration with wearable devices  
- Machine learning-based classification of cardiac conditions  
- Improved interactive dashboard interface  

Author

Biomedical Signal Processing Lab   
Student: Areej umer
