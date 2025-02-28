from pathlib import Path 
from obspy.core import Stream, Trace, UTCDateTime
from obspy.signal.konnoohmachismoothing import konno_ohmachi_smoothing
import pandas as pd 
import numpy as np
from config import *
import utilities
from response_spectra_scripts.response_spectrum import NigamJennings, plot_response_spectra, plot_time_series

def get_record_arrivals(stream: Stream) -> tuple:
    arrivals = {
        "20140126_135529_VSK1": {"Parr": 18, "Sarr": 23},
        "20140126_135537_ARG2": {"Parr": 8, "Sarr": 12},
        "20140126_135537_ZAK2": {"Parr": 15, "Sarr": 30}
    }

    record_name = utilities.get_record_name(stream)
    
    if record_name not in arrivals:
        return None, f"Record {record_name} does not have any arrivals!"

    record_arrivals = arrivals[record_name]

    error_message = utilities.validate_arrivals(stream, record_arrivals)
    
    return record_arrivals, error_message

def create_stream_from_txt(txt_file_path: Path) -> tuple:
    try:
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

            st = Stream(traces=traces)

            error = utilities.validate_stream(st)
            
            return st, error
    except Exception as e:
        return None, str(e)

    
def process_noise_signal_streams(st_noise: Stream, st_signal: Stream) -> tuple:
    try:
        st_noise.taper(None, type=AppParameters.TAPER_TYPE.value, max_length=AppParameters.TAPER_MAX_LENGTH.value, side=AppParameters.TAPER_SIDE.value)
        st_signal.taper(None, type=AppParameters.TAPER_TYPE.value, max_length=AppParameters.TAPER_MAX_LENGTH.value, side=AppParameters.TAPER_SIDE.value)
        return (st_noise, st_signal), None
    except Exception as e:
        return None, str(e)

def generate_noise_signal_windows(stream: Stream, Parr: float, Sarr: float) -> tuple:
    first_trace = stream.traces[0]
    starttime = first_trace.stats.starttime

    noise_trim_left = Parr - AppParameters.WINDOW_LENGTH.value - 1
    noise_trim_right = Parr + 1
    signal_trim_left = Sarr - 1
    signal_trim_right = Sarr + AppParameters.WINDOW_LENGTH.value + 1

    st_noise = stream.copy() # copy for noise stream
    st_signal = stream.copy() # copy for signal stream
   
    try:
        st_noise.trim(starttime=starttime+noise_trim_left, endtime=starttime+noise_trim_right)
        st_signal.trim(starttime=starttime+signal_trim_left, endtime=starttime+signal_trim_right)
    except Exception as e:
        return None, f"Cannot trim the trace to create a noise and a signal part: {str(e)}"
    
    return (st_noise, st_signal), None
        
    
def pre_process_stream(stream: Stream) -> tuple:
    try:
        stream.filter(
            AppParameters.FILTER_TYPE.value, 
            freqmin=AppParameters.FILTER_FREQ_MIN.value, 
            freqmax=AppParameters.FILTER_FREQ_MAX.value, 
            corners=AppParameters.FILTER_CORNERS.value
        )
        # stream.detrend(type=AppParameters.DETREND_TYPE.value)
        return stream, None
    except Exception as e:
        return None, str(e)
    

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
    fas_freqs[fas_freqs == 0] = np.nan
    fas_freqs_interp = np.logspace(
        np.log10(AppParameters.FOURIER_MIN_FREQ.value), 
        np.log10(AppParameters.FOURIER_MAX_FREQ.value), 
        num=AppParameters.FOURIER_TOTAL_FREQS.value
    )

 # fas_amps_interp = np.interp(fas_freqs_interp, fas_freqs, fft_amp_abs)
    fas_amps_interp = np.power(10, np.interp(np.log10(fas_freqs_interp), np.log10(fas_freqs), np.log10(fft_amp_abs)))
    
    fas_amps_konno = konno_ohmachi_smoothing(
        fas_amps_interp, 
        fas_freqs_interp, 
        bandwidth=AppParameters.KONNO_OMACHI_BANDWIDTH.value, 
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
        signal_to_noise_ratio>AppParameters.SIGNAL_TO_NOISE.value, 
        signal_fas_amps, 
        np.nan
    )

    return signal_fas_amps_filtered

def compute_response_spectra(trace: Trace) -> dict:
    periods = np.linspace(
        AppParameters.RESPONSE_SPECTRA_MIN_PERIOD.value, 
        AppParameters.RESPONSE_SPECTRA_MAX_PERIOD.value, 
        AppParameters.RESPONSE_SPECTRA_TOTAL_PERIODS.value, 
    )
    rs = NigamJennings(
        trace.data, 
        1/trace.stats.sampling_rate, 
        periods, 
        damping=AppParameters.RESPONSE_SPECTRA_DUMPING.value, 
        units="m/s/s"
    )
    spec, ts, acc, vel, dis = rs.evaluate()
    return {
        "displacement": dis,
        "acceleration": acc, 
        "velocity": vel,
        "spec": spec,
        "period": periods
    }
