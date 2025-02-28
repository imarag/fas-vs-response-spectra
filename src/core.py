import functions as functions 
import utilities as utilities
from config import *

setup_environment()

for seismic_file in AppRoutes.DATA_FOLDER_PATH.value.iterdir():

    handle_info(f"processing: {seismic_file}...")

    stream, error = functions.create_stream_from_txt(seismic_file)
    if error is not None:
        handle_error(f"Cannot convert txt file '{seismic_file}' to mseed: {error}")
        continue
   
    utilities.plot_stream(stream,  title=f"Initial records")

    stream, error = functions.pre_process_stream(stream)
    if error is not None:
        handle_error(f"Cannot preprocess the stream: {error}")
        continue

    utilities.plot_stream(stream,  title=f"Filtered records ({str(AppParameters.FILTER_FREQ_MIN.value).replace('.', ',')}-{str(AppParameters.FILTER_FREQ_MAX.value).replace('.', ',')} Hz)")

    ps_arrivals, error = functions.get_record_arrivals(stream)
    if error is not None:
        handle_error(f"Cannot generate record P & S arrivals: {error}")
        continue 

    Parr = ps_arrivals["Parr"]
    Sarr = ps_arrivals["Sarr"]

    utilities.plot_stream(stream,  title=f"Arrivals Selection Parr={str(Parr).replace('.', ',')} & Sarr={str(Sarr).replace('.', ',')}", parr=Parr, sarr=Sarr)

    ps_windows, error = functions.generate_noise_signal_windows(stream, Parr, Sarr)
    if error is not None:
        handle_error(f"Cannot create the noise or the signal window: {error}")
        continue 

    st_noise, st_signal = ps_windows

    processed_ps_windows, error = functions.process_noise_signal_streams(st_noise, st_signal)
    if error is not None:
        handle_error(f"Cannot apply preprocessing steps to the noise and signal windows: {error}")
        continue 

    st_noise, st_signal = processed_ps_windows

    utilities.plot_stream(st_noise,  title=f"Trimmed noise window")
    utilities.plot_stream(st_signal,  title=f"Trimmed signal window")
    
    for i in range(len(stream)): # loop at each trace
        tr_noise = st_noise.traces[i]
        tr_signal = st_signal.traces[i]
        
        tr_noise_dict = functions.compute_fourier(tr_noise)
        tr_signal_dict = functions.compute_fourier(tr_signal)
        
        tr_signal_filtered = functions.apply_signal_to_noise_ratio(
            tr_noise_dict["fas_amps_konno"], tr_signal_dict["fas_amps_konno"]
        )

        unprocessed_trace = stream.traces[i]
        response_dict = functions.compute_response_spectra(unprocessed_trace)

        utilities.plot_FAS_response_spectra(tr_noise_dict, tr_signal_dict, response_dict, tr_noise.stats.channel)

cleanup_resources()

    

    