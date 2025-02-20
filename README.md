# FAS versus Acceleration Response Spectra
This repository provides a structured workflow for transforming seismic data from TXT files to MiniSEED format and conducting spectral analysis. The process includes filtering, detrending, Fourier analysis, signal-to-noise ratio calculations, and response spectra computations.

## Pipeline Overview

1. TXT to MiniSEED Conversion – Converts raw seismic acceleration data from text files to MiniSEED format.
2. Filtering – Applies a bandpass filter using the ObsPy bandpass filter.
3. Detrending – Removes trends from all components (ObsPy detrend).
4. Arrival Selection – Identifies P and S wave arrivals based on manual inspection.
5. Noise Window Selection – Defines the noise window from starttime + Parr - window_length - 1 to starttime + Parr + 1.
6. Signal Window Selection – Defines the signal window from starttime + Sarr - 1 to starttime + Sarr + window_length + 1.
7. Detrending of Windows – Re-applies detrending (type="simple") to both noise and signal windows.
8. Tapering – Applies Parzen tapering to the noise and signal windows.
9. Fourier Transform – Computes Fourier Amplitude Spectra (FAS) for noise and signal components.
10. Frequency Interpolation – Interpolates FAS at n logarithmically spaced frequencies.
11. Konno-Ohmachi Smoothing – Applies Konno-Ohmachi smoothing with a specific bandwidth.
12. Signal-to-Noise Ratio (SNR) Filtering – Retains frequencies where SNR > n.
13. Response Spectra Computation – Computes response spectra from raw waveforms (before windowing), following the USGS method.
14. Response Spectra Plotting – Frequencies vs Response spectra computed as pseudo velocity

Technologies Used:
- ObsPy for seismic data processing
- NumPy / SciPy for signal processing
- Matplotlib for visualization

This repository is useful for researchers working on seismic data preprocessing, spectral analysis, and engineering seismology.
