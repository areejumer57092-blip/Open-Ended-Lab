import numpy as np
import pandas as pd
from scipy.signal import find_peaks, butter, filtfilt, welch
from scipy.interpolate import CubicSpline

class SignalProcessing:
    @staticmethod
    def filter_ecg(data, fs=250):
        """
        Applies a zero-phase Butterworth Bandpass filter (0.5 to 45 Hz)
        to remove baseline wander and suppress high-frequency noise.
        """
        nyq = 0.5 * fs
        low = 0.5 / nyq
        high = 45.0 / nyq
        # We handle boundary cases where fs might be very low
        if high >= 1.0:
            high = 0.99
            
        b, a = butter(3, [low, high], btype='band')
        filtered = filtfilt(b, a, data)
        return filtered

    @staticmethod
    def detect_peaks(data, fs=250):
        """
        Detect R-peaks in ECG signal using scipy prominently,
        invariant to absolute baseline altitudes.
        """
        dynamic_prominence = (np.percentile(data, 99) - np.median(data)) * 0.5
        min_dist = int(0.2 * fs)
        
        peaks, properties = find_peaks(data, prominence=dynamic_prominence, distance=min_dist)
        return peaks, data[peaks]

    @staticmethod
    def calculate_nn_intervals(peaks, fs=250):
        """
        Calculates NN intervals (ms) with Ectopic Beat Rejection.
        RR intervals differing > 20% from a rolling 5-beat average are suppressed.
        """
        diff_samples = np.diff(peaks)
        raw_rr = (diff_samples / fs) * 1000
        
        if len(raw_rr) < 5:
            return raw_rr
            
        nn = [raw_rr[0]]
        for i in range(1, len(raw_rr)):
            start_idx = max(0, len(nn) - 5)
            local_mean = np.mean(nn[start_idx:])
            
            # Quotient rule constraint for Sinus rhythm
            if abs(raw_rr[i] - local_mean) <= 0.20 * local_mean:
                nn.append(raw_rr[i])
                
        return np.array(nn)

    @staticmethod
    def calc_time_domain(nn):
        """
        Computes standard time-domain metrics.
        """
        if len(nn) == 0:
            return {}
        
        mean_nn = np.mean(nn)
        hr = 60000 / mean_nn if mean_nn > 0 else 0
        sdnn = np.std(nn, ddof=1)
        
        diff_nn = np.diff(nn)
        rmssd = np.sqrt(np.mean(diff_nn**2)) if len(diff_nn) > 0 else 0
        
        nn50 = np.sum(np.abs(diff_nn) > 50)
        pnn50 = (nn50 / len(diff_nn)) * 100 if len(diff_nn) > 0 else 0
        
        return {
            'mean_rr': f"{mean_nn:.1f}",
            'hr': f"{hr:.0f}",
            'sdnn': f"{sdnn:.1f}",
            'rmssd': f"{rmssd:.1f}",
            'pnn50': f"{pnn50:.1f}"
        }

    @staticmethod
    def calc_poincare(nn):
        """
        Extracts SD1, SD2 and points for Poincaré Plot.
        """
        if len(nn) < 2:
            return {'x': [], 'y': [], 'sd1': "0.0", 'sd2': "0.0", 'ratio': "0.0"}
            
        x = nn[:-1]
        y = nn[1:]
        
        sd1 = np.std(np.subtract(x, y) / np.sqrt(2), ddof=1)
        sd2 = np.std(np.add(x, y) / np.sqrt(2), ddof=1)
        ratio = sd1 / sd2 if sd2 > 0 else 0
        
        return {
            'x': x,
            'y': y,
            'sd1': f"{sd1:.2f}",
            'sd2': f"{sd2:.2f}",
            'ratio': f"{ratio:.2f}"
        }

    @staticmethod
    def calc_frequency_domain(nn):
        """
        Calculates True Power Spectral Density (PSD) using Welch's Method via 
        interpolating the NN interval tachogram continuously at 4 Hz.
        """
        if len(nn) < 10:
            return {'freqs': [], 'psd': [], 'lf': "0.0", 'hf': "0.0", 'lfhf': "0.0"}
            
        nn_sec = nn / 1000.0
        time_axis = np.cumsum(nn_sec)
        time_axis -= time_axis[0]
        
        # Resample tachogram uniformly at 4 Hz
        fs_interp = 4.0
        time_interp = np.arange(0, time_axis[-1], 1/fs_interp)
        
        try:
            cs = CubicSpline(time_axis, nn_sec)
            nn_interp = cs(time_interp)
        except Exception:
            return {'freqs': [], 'psd': [], 'lf': "0.0", 'hf': "0.0", 'lfhf': "0.0"}
        
        nn_interp -= np.mean(nn_interp)
        nperseg = min(256, len(nn_interp))
        if nperseg < 32:
            return {'freqs': [], 'psd': [], 'lf': "0.0", 'hf': "0.0", 'lfhf': "0.0"}
            
        freqs, psd = welch(nn_interp, fs=fs_interp, nperseg=nperseg)
        
        lf_mask = (freqs >= 0.04) & (freqs <= 0.15)
        hf_mask = (freqs > 0.15) & (freqs <= 0.4)
        
        lf_power = np.trapezoid(psd[lf_mask], freqs[lf_mask]) * 1000 
        hf_power = np.trapezoid(psd[hf_mask], freqs[hf_mask]) * 1000 
        
        ratio = lf_power / hf_power if hf_power > 0 else 0
        plot_mask = freqs <= 0.4
        
        return {
            'freqs': freqs[plot_mask],
            'psd': psd[plot_mask],
            'lf': f"{lf_power:.1f}",
            'hf': f"{hf_power:.1f}",
            'lfhf': f"{ratio:.2f}"
        }

    @staticmethod
    def calc_sample_entropy(nn, m=2, r_multiplier=0.2):
        """
        Calculates Sample Entropy (SampEn) for the NN intervals via fast numpy broadcasting.
        """
        if len(nn) < 50:
            return "N/A"
            
        nn_arr = np.array(nn)
        r = r_multiplier * np.std(nn_arr)
        N = len(nn_arr)
        
        def _phi(m):
            # Form templates of length m
            if N - m + 1 <= 0: return 0
            x = np.array([nn_arr[i:i+m] for i in range(N - m + 1)])
            # Vectorized Chebyshev distances: max(|x[i] - x[j]|)
            C = np.sum(np.max(np.abs(x[:, None, :] - x[None, :, :]), axis=2) <= r, axis=0) - 1
            return np.sum(C)

        B = _phi(m)
        A = _phi(m + 1)
        
        if A == 0 or B == 0:
            return "N/A"
            
        sampen = -np.log(A / B)
        return f"{sampen:.3f}"

    @staticmethod
    def calc_segmentwise(nn, window=60):
        if len(nn) < window + 10:
            return {'hr': [], 'rmssd': [], 'sd_ratio': [], 'hf': []}
            
        hr_list, rmssd_list, sd_list, hf_list = [], [], [], []
        
        for i in range(len(nn) - window):
            chunk = nn[i:i+window]
            
            mean_nn = np.mean(chunk)
            hr = 60000 / mean_nn if mean_nn > 0 else 0
            
            diffs = np.diff(chunk)
            rmssd = np.sqrt(np.mean(diffs**2)) if len(diffs) > 0 else 0
            
            x = chunk[:-1]
            y = chunk[1:]
            sd1 = np.std(np.subtract(x, y) / np.sqrt(2), ddof=1)
            sd2 = np.std(np.add(x, y) / np.sqrt(2), ddof=1)
            ratio = (sd1 / sd2 * 10) if sd2 > 0 else 0 
            
            hf = 0
            try:
                nn_sec = chunk / 1000.0
                time_axis = np.cumsum(nn_sec)
                time_axis -= time_axis[0]
                fs_interp = 4.0
                if len(time_axis) > 10 and time_axis[-1] > 2:
                    time_interp = np.arange(0, time_axis[-1], 1/fs_interp)
                    cs = CubicSpline(time_axis, nn_sec)
                    nn_interp = cs(time_interp)
                    nn_interp -= np.mean(nn_interp)
                    nperseg = min(64, len(nn_interp))
                    if nperseg >= 16:
                        freqs, psd = welch(nn_interp, fs=fs_interp, nperseg=nperseg)
                        hf_mask = (freqs > 0.15) & (freqs <= 0.4)
                        hf = np.trapezoid(psd[hf_mask], freqs[hf_mask]) * 1000
            except Exception:
                hf = 0
                
            hr_list.append(hr)
            rmssd_list.append(rmssd)
            sd_list.append(ratio)
            hf_list.append(hf)
            
        if len(hf_list) > 5:
            # Smooth outputs natively to match the elegant UI rendering of the reference
            hf_list = np.convolve(hf_list, np.ones(5)/5, mode='same').tolist()
            sd_list = np.convolve(sd_list, np.ones(5)/5, mode='same').tolist()
            rmssd_list = np.convolve(rmssd_list, np.ones(3)/3, mode='same').tolist()
            
        return {'hr': hr_list, 'rmssd': rmssd_list, 'sd_ratio': sd_list, 'hf': hf_list}

    @staticmethod
    def generate_mock_ecg(fs=250, seconds=60):
        length = fs * seconds
        time = np.linspace(0, seconds, length)
        hr_base = 65
        data = np.zeros(length)
        rsa = np.sin(2 * np.pi * 0.2 * time) * 0.15
        
        current_phase = 0
        for i in range(length):
            t = time[i]
            bw = np.sin(2 * np.pi * 0.5 * t) * 0.1
            interval = (60 / hr_base) + rsa[i]
            interval_samples = int(interval * fs)
            
            val = bw
            if current_phase > 20 and current_phase < 40:
                val += 0.15 * np.sin(np.pi * (current_phase - 20) / 20)
            elif 60 < current_phase < 70:
                val -= 0.2
            elif 70 <= current_phase < 80:
                val += 1.5
            elif 80 <= current_phase < 90:
                val -= 0.4
            elif 120 < current_phase < 170:
                val += 0.3 * np.sin(np.pi * (current_phase - 120) / 50)
                
            val += np.random.normal(0, 0.02)
            data[i] = val
            
            current_phase += 1
            if current_phase >= interval_samples:
                current_phase = 0
                
        return data
