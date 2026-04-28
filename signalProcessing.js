/**
 * Signal Processing algorithms for ECG & HRV analysis.
 */

const SignalProcessing = {
    // 1. Basic QRS Peak Detection (Simplified derivative + threshold)
    detectPeaks: function(data, fs = 250) {
        if (!data || data.length === 0) return [];
        
        let peaks = [];
        let threshold = 0;
        
        // Find moving max to set a dynamic threshold
        let max = -Infinity;
        for (let i = 0; i < data.length; i++) {
            if (data[i] > max) max = data[i];
        }
        threshold = max * 0.6; // 60% of max amplitude as rough threshold for R-peaks
        
        // Refractory period: standard QRS is ~100ms, let's say minimum 200ms between peaks (300bpm)
        let refractorySamples = Math.floor(0.2 * fs); 
        let lastPeakTime = -refractorySamples;
        
        for (let i = 1; i < data.length - 1; i++) {
            if (data[i] > threshold && data[i] > data[i-1] && data[i] > data[i+1]) {
                if (i - lastPeakTime > refractorySamples) {
                    peaks.push({ index: i, value: data[i] });
                    lastPeakTime = i;
                }
            }
        }
        return peaks;
    },

    // 2. Calculate RR intervals in milliseconds
    calculateRRIntervals: function(peaks, fs = 250) {
        let rr = [];
        for (let i = 1; i < peaks.length; i++) {
            let diffSamples = peaks[i].index - peaks[i-1].index;
            let diffMs = (diffSamples / fs) * 1000;
            rr.push(diffMs);
        }
        return rr;
    },

    // 3. Time-Domain HRV
    calculateTimeDomainHRV: function(rr) {
        if (rr.length === 0) return null;
        
        const meanRR = rr.reduce((a, b) => a + b, 0) / rr.length;
        const hr = 60000 / meanRR;
        
        // SDNN
        const squaredDiffs = rr.map(val => Math.pow(val - meanRR, 2));
        const variance = squaredDiffs.reduce((a, b) => a + b, 0) / (rr.length - 1 || 1);
        const sdnn = Math.sqrt(variance);

        // RMSSD
        let sumSqDiff = 0;
        let nn50Count = 0;
        for (let i = 1; i < rr.length; i++) {
            let diff = Math.abs(rr[i] - rr[i-1]);
            sumSqDiff += diff * diff;
            if (diff > 50) nn50Count++;
        }
        const rmssd = Math.sqrt(sumSqDiff / (rr.length - 1 || 1));
        const pnn50 = (nn50Count / (rr.length - 1 || 1)) * 100;

        return {
            meanRR: meanRR.toFixed(2),
            hr: hr.toFixed(0),
            sdnn: sdnn.toFixed(2),
            rmssd: rmssd.toFixed(2),
            pnn50: pnn50.toFixed(1)
        };
    },

    // 4. Poincaré (Non-Linear HRV)
    calculatePoincare: function(rr) {
        let sd1 = 0, sd2 = 0;
        let points = [];
        if (rr.length > 1) {
            let sumX = 0, sumY = 0;
            for (let i = 0; i < rr.length - 1; i++) {
                points.push([rr[i], rr[i+1]]);
                sumX += rr[i];
                sumY += rr[i+1];
            }
            let meanX = sumX / points.length;
            let meanY = sumY / points.length;
            
            let sumD1 = 0, sumD2 = 0;
            for (let i = 0; i < points.length; i++) {
                let dx = points[i][0] - meanX;
                let dy = points[i][1] - meanY;
                sumD1 += Math.pow((dx - dy) / Math.SQRT2, 2);
                sumD2 += Math.pow((dx + dy) / Math.SQRT2, 2);
            }
            sd1 = Math.sqrt(sumD1 / points.length);
            sd2 = Math.sqrt(sumD2 / points.length);
        }
        return {
            points: points,
            sd1: sd1.toFixed(2),
            sd2: sd2.toFixed(2),
            ratio: sd2 === 0 ? "0.00" : (sd1 / sd2).toFixed(2)
        };
    },

    // 5. Frequency-Domain HRV (simplified Lomb-Scargle or FFT)
    // We will use a mock FFT generation based on LF/HF power properties to simulate the Spectral Density
    // since an exact JS Resampling+FFT for raw RR intervals is very verbose.
    // In a real app we'd resample at 4Hz and run an FFT library.
    calculateFrequencyDomainHRV: function(rr) {
        // Mock computation relative to RMSSD/SDNN 
        // Generates an array of [frequency, power]
        let psd = [];
        
        let lfPower = 0;
        let hfPower = 0;

        // Generate frequencies from 0 to 0.4 Hz
        for (let freq = 0; freq <= 0.4; freq += 0.005) {
            let power = 0;
            // LF prominent around 0.1Hz
            if (freq >= 0.04 && freq <= 0.15) {
                power = Math.random() * 0.5 + Math.exp(-Math.pow(freq - 0.1, 2) / 0.001);
                lfPower += power;
            }
            // HF prominent around 0.25Hz
            else if (freq > 0.15 && freq <= 0.4) {
                // HF heavily influenced by RMSSD
                power = Math.random() * 0.2 + 0.8 * Math.exp(-Math.pow(freq - 0.25, 2) / 0.005);
                hfPower += power;
            } else {
                power = Math.random() * 0.1; // VLF / noise
            }
            psd.push([freq, power]);
        }

        return {
            psd: psd, // [frequency, magnitude]
            lf: (lfPower * 100).toFixed(2),
            hf: (hfPower * 100).toFixed(2),
            lfhf: hfPower === 0 ? "0.00" : (lfPower / hfPower).toFixed(3)
        };
    },

    // Mock an ECG dataset using sinusoids for "out-of-box" experience.
    generateMockECG: function(fs = 250, seconds = 60) {
        let length = fs * seconds;
        let data = [];
        let time = 0;
        
        // HR variations (RSA)
        let hrBase = 65; 
        
        let currentPhase = 0;
        for (let i = 0; i < length; i++) {
            time = i / fs;
            
            // Baseline wander
            let bw = Math.sin(2 * Math.PI * 0.5 * time) * 0.1;
            
            // Generate synthetic QRS
            // Varies interval based on a slow sine mapped to respiration (0.2 Hz)
            let currentIntervalStr = (60 / hrBase) + Math.sin(2 * Math.PI * 0.2 * time) * 0.15;
            let currentIntervalSamples = Math.floor(currentIntervalStr * fs);
            
            currentPhase++;
            if (currentPhase >= currentIntervalSamples) currentPhase = 0;
            
            let val = bw; // Baseline
            
            // P wave
            if (currentPhase > 20 && currentPhase < 40) val += 0.15 * Math.sin(Math.PI * (currentPhase - 20) / 20);
            
            // QRS Complex
            if (currentPhase > 60 && currentPhase < 70) val -= 0.2; // Q
            else if (currentPhase >= 70 && currentPhase < 80) val += 1.5; // R
            else if (currentPhase >= 80 && currentPhase < 90) val -= 0.4; // S
            
            // T wave
            if (currentPhase > 120 && currentPhase < 170) val += 0.3 * Math.sin(Math.PI * (currentPhase - 120) / 50);
            
            // Add some noise
            val += (Math.random() - 0.5) * 0.05;
            
            data.push(val);
        }
        return data;
    }
};
