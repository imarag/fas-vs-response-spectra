from pathlib import Path 
from obspy.core import Stream, Trace, UTCDateTime
from obspy.signal.konnoohmachismoothing import konno_ohmachi_smoothing
import pandas as pd 
import numpy as np
from config import *
from response_spectrum import NigamJennings, plot_response_spectra, plot_time_series

def get_record_arrivals(record_name) -> dict | None:
    arrivals = {
        "20140126_135529_VSK1": {"Parr": 18, "Sarr": 23},
        "20140126_135537_ARG2": {"Parr": 8, "Sarr": 12},
        "20140126_135537_ZAK2": {"Parr": 15, "Sarr": 30}
    }
    
    if record_name not in arrivals:
        return None

    record_arrivals = arrivals[record_name]
    return record_arrivals

def create_stream_from_txt(txt_file_path: Path) -> Stream:
    with open(txt_file_path, "r") as file:
        file_contents = file.readlines()
        station = file_contents[1].strip().split(":")[1].strip()
        starttime = UTCDateTime(file_contents[2].strip().split(":", 1)[1])
        fs = float(file_contents[3].split(":")[1].strip(" HhZz\n"))
        npts = int(file_contents[4].split(":")[1].strip())
        components = file_contents[7].split(":")[1].split()
        components = [c.strip() for c in components]
        df = pd.DataFrame([row.strip().split() for row in file_contents[10:]])
        df.columns = components

        stats = {"npts": npts, "sampling_rate": fs, "station": station, "starttime": starttime}

        traces = []
        for c in components:
            data = pd.to_numeric(df[c]).to_numpy()
            header = stats
            header["component"] = c
            tr = Trace(data=data, header=header)
            traces.append(tr)

        return Stream(traces = traces)
    


def compute_fourier(tr: Trace) -> dict:
    tr_stats = tr.stats
    sampling_rate = tr_stats.sampling_rate
    npts = tr_stats.npts
    delta = tr_stats.delta
    sl = int(npts / 2)
    fnyq = sampling_rate / 2

    fas_freqs = np.linspace(0, fnyq, sl)
    fft_amp = np.fft.fft(tr.data[:npts])
    fft_amp_abs = delta * np.abs(fft_amp)[0:sl]

    fas_freqs_interp = np.logspace(
        np.log10(FOURIER_MIN_FREQ), 
        np.log10(FOURIER_MAX_FREQ), 
        num=FOURIER_TOTAL_FREQS
    )
    fas_amps_interp = np.interp(fas_freqs_interp, fas_freqs, fft_amp_abs)
    
    fas_amps_konno = konno_ohmachi_smoothing(
        fas_amps_interp, 
        fas_freqs_interp, 
        bandwidth=KONNO_OMACHI_BANDWIDTH, 
        normalize=True
    )
    
    return {
        "component": tr_stats.component,
        "fas_freqs": np.array(fas_freqs),
        "fas_amps":  np.array(fft_amp_abs),
        "fas_freqs_interp": np.array(fas_freqs_interp),
        "fas_amps_interp": np.array(fas_amps_interp),
        "fas_amps_konno": np.array(fas_amps_konno)
    }

def apply_signal_to_noise_ratio(noise_fas_amps: np.ndarray, signal_fas_amps: np.ndarray) -> np.ndarray:
    signal_to_noise_ratio = signal_fas_amps / noise_fas_amps
        
    signal_fas_amps_filtered = np.where(
        signal_to_noise_ratio>SIGNAL_TO_NOISE, 
        signal_fas_amps, 
        np.nan
    )

    return signal_fas_amps_filtered

def compute_response_spectra(trace: Trace) -> dict:
    periods = np.linspace(0.01, 20, 300)
    rs = NigamJennings(trace.data, 1/trace.stats.sampling_rate, periods, damping=0.5, units="m/s/s")
    spec, ts, acc, vel, dis = rs.evaluate()
    return {
        "displacement": dis,
        "acceleration": acc, 
        "velocity": vel,
        "spec": spec,
        "period": periods
    }
