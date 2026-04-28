// ECharts Instances
let waveformChart, poincareChart, psdChart, segmentChart, globalReturnChart;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    
    // Bind buttons
    document.getElementById('loadSampleBtn').addEventListener('click', loadSampleData);
    
    const fileInput = document.getElementById('fileUpload');
    fileInput.addEventListener('change', handleFileUpload);
});

function initCharts() {
    // Top Waveform
    waveformChart = echarts.init(document.getElementById('chart-waveform'));
    
    // Middle Row
    poincareChart = echarts.init(document.getElementById('chart-poincare'));
    psdChart = echarts.init(document.getElementById('chart-psd'));
    
    // Bottom Row
    segmentChart = echarts.init(document.getElementById('chart-segment'));
    globalReturnChart = echarts.init(document.getElementById('chart-global-return'));

    window.addEventListener('resize', () => {
        waveformChart.resize();
        poincareChart.resize();
        psdChart.resize();
        segmentChart.resize();
        globalReturnChart.resize();
    });
}

function updateStatus(text, color = "var(--accent-yellow)") {
    const el = document.getElementById('statusIndicator');
    el.innerText = text;
    el.style.color = color;
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    updateStatus("Parsing File...", "var(--accent-cyan)");
    
    Papa.parse(file, {
        complete: function(results) {
            updateStatus("Processing Data...", "var(--accent-cyan)");
            
            // Assume single column or flatten dynamically
            // Try to intelligently extract just the values
            let ecgData = [];
            for (let row of results.data) {
                // If single value per row
                if (row.length > 0) {
                    // Try to guess the column that contains ECG (usually purely numbers and floating)
                    for (let col of row) {
                        let parsed = parseFloat(col);
                        if (!isNaN(parsed) && col.trim() !== "") {
                            ecgData.push(parsed);
                            break; // just take the first valid number per row assuming it's a single trace
                        }
                    }
                }
            }
            
            if (ecgData.length < 500) {
                alert("File doesn't contain enough valid numeric data or is not formatted correctly.");
                updateStatus("Error Reading Data", "red");
                return;
            }

            processData(ecgData, 250); // Assuming 250Hz sampling for uploaded datasets if not specified
        },
        error: function(err) {
            alert("Error parsing CSV: " + err.message);
            updateStatus("Error Parsing", "red");
        }
    });
}

function loadSampleData() {
    updateStatus("Generating Sample...", "var(--accent-cyan)");
    // Generate 60 seconds (1 minute) of synthetic ECG data
    const fs = 250;
    const data = SignalProcessing.generateMockECG(fs, 60);
    processData(data, fs);
}

function processData(data, fs) {
    updateStatus("Running peak detection...", "var(--accent-yellow)");
    
    const peaks = SignalProcessing.detectPeaks(data, fs);
    const rrIntervals = SignalProcessing.calculateRRIntervals(peaks, fs);
    
    updateStatus("Calculating metrics...", "var(--accent-yellow)");
    
    const timeDomain = SignalProcessing.calculateTimeDomainHRV(rrIntervals);
    const nonlinear = SignalProcessing.calculatePoincare(rrIntervals);
    const freqDomain = SignalProcessing.calculateFrequencyDomainHRV(rrIntervals);
    
    // Update Table
    updateTable(timeDomain, nonlinear, freqDomain);
    
    // Update Charts
    updateWaveform(data, peaks, fs);
    updatePoincare(nonlinear.points);
    updatePSD(freqDomain.psd);
    updateSegment(rrIntervals);
    
    updateStatus("Analysis Complete", "var(--accent-green)");
}

function updateTable(td, nl, fd) {
    document.getElementById('val-meanrr').innerText = td.meanRR + " ms";
    document.getElementById('val-hr').innerText = td.hr + " bpm";
    document.getElementById('val-sdnn').innerText = td.sdnn + " ms";
    document.getElementById('val-rmssd').innerText = td.rmssd + " ms";
    document.getElementById('val-pnn50').innerText = td.pnn50 + " %";
    
    document.getElementById('val-sd1').innerText = nl.sd1;
    document.getElementById('val-sd2').innerText = nl.sd2;
    document.getElementById('val-sdratio').innerText = nl.ratio;
    
    document.getElementById('val-lf').innerText = fd.lf + " ms²";
    document.getElementById('val-hf').innerText = fd.hf + " ms²";
    document.getElementById('val-lfhf').innerText = fd.lfhf;
}

// ---------------- Charts Setup ----------------

// 1. Raw Waveform (First 10s only per instructions)
function updateWaveform(data, peaks, fs) {
    let tenSecondsSamples = fs * 10;
    let slicedData = data.slice(0, Math.min(tenSecondsSamples, data.length));
    
    // Map data to time
    let timeSeries = slicedData.map((val, i) => [i / fs, val]);
    
    // Filter peaks that are within the first 10 seconds
    let peakPoints = peaks
        .filter(p => p.index < tenSecondsSamples)
        .map(p => {
            return {
                coord: [p.index / fs, p.value],
                itemStyle: { color: 'var(--accent-magenta)' }
            };
        });

    waveformChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { 
            type: 'value', 
            name: 'Time (s)',
            scale: true,
            splitLine: { show: false },
            axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        yAxis: { 
            type: 'value',
            splitLine: { show: true, lineStyle: { color: 'var(--panel-border)' } },
            axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        series: [{
            name: 'ECG',
            type: 'line',
            showSymbol: false,
            data: timeSeries,
            lineStyle: { color: 'var(--accent-cyan)', width: 1.5 },
            markPoint: {
                symbol: 'circle',
                symbolSize: 6,
                data: peakPoints
            }
        }],
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20 }]
    });
}

// 2. Poincare (Local/Global context mapping)
function updatePoincare(points) {
    const poincareOptions = {
        grid: { left: '10%', right: '10%', top: '10%', bottom: '15%' },
        xAxis: { 
            name: 'RR_n (ms)', 
            type: 'value', scale: true,
            splitLine: { show: false },
            axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        yAxis: { 
            name: 'RR_n+1 (ms)', 
            type: 'value', scale: true,
            splitLine: { show: false },
            axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        series: [{
            type: 'scatter',
            symbolSize: 4,
            data: points,
            itemStyle: { color: 'var(--text-primary)', opacity: 0.6 }
        }]
    };

    // Both get the same basic layout but Local is a subset if doing time segments.
    // For this app, Global is all points, Local would be a scrolling window. 
    // We will just map all points for simplicity.
    poincareChart.setOption(poincareOptions);
    globalReturnChart.setOption(poincareOptions);
}

// 3. PSD - Spectra of RR
function updatePSD(psd) {
    psdChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '15%', right: '5%', top: '10%', bottom: '15%' },
        xAxis: { 
            name: 'Frequency (Hz)', 
            type: 'value',
            splitLine: { show: false },
            axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        yAxis: { 
            name: 'Power', 
            type: 'value',
            splitLine: { show: false },
            axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        visualMap: {
            show: false,
            dimension: 0,
            pieces: [
                { lte: 0.04, color: 'var(--text-secondary)' }, // VLF
                { gt: 0.04, lte: 0.15, color: 'var(--accent-green)' }, // LF
                { gt: 0.15, color: 'var(--accent-yellow)' } // HF
            ]
        },
        series: [{
            type: 'line',
            showSymbol: false,
            data: psd,
            areaStyle: { opacity: 0.3 }
        }]
    });
}

// 4. Segmentwise HRV
function updateSegment(rr) {
    // Generate a quick moving average of RR to show trends over time
    let trend = [];
    let windowSize = 10;
    for (let i = 0; i < rr.length - windowSize; i++) {
        let avg = 0;
        for (let j = 0; j < windowSize; j++) {
            avg += rr[i+j];
        }
        trend.push([i, avg / windowSize]);
    }

    segmentChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '10%', right: '5%', top: '10%', bottom: '15%' },
        xAxis: { 
            name: 'Beat Index',
            type: 'category',
            splitLine: { show: false },
             axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        yAxis: { 
            name: 'RR Interval Trend (ms)',
            type: 'value', scale: true,
            splitLine: { show: true, lineStyle: { color: 'var(--panel-border)' } },
            axisLine: { lineStyle: { color: 'var(--text-secondary)' } }
        },
        series: [{
            type: 'line',
            showSymbol: false,
            data: trend.map(t => t[1]),
            lineStyle: { width: 2, color: 'var(--accent-blue)' }
        }]
    });
}
