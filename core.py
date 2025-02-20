import functions 
import utilities
import logging 
from config import *


figures_pdf = PdfPages('figures.pdf')

for seismic_file in DATA_FOLDER_PATH.iterdir():

    logging.info(f"processing: {seismic_file}...")
    print(f"processing: {seismic_file}...")
 
    try:
        stream = functions.create_stream_from_txt(seismic_file)
    except Exception as e:
        logging.error(f"Cannot convert txt file '{seismic_file}' to mseed: {str(e)}")
        continue

    error_message = utilities.validate_stream(stream)

    if error_message is not None:
        logging.error(f"The stream generated from '{seismic_file}' did not pass the validation: {error_message}")
        continue

    record_name = utilities.get_record_name(stream)
   
    plot_initial = utilities.plotStreams(stream,  title=f"Initial records - {record_name}")
    figures_pdf.savefig(plot_initial)
    plt.close(plot_initial)

    try:
        stream.filter(
            FILTER_TYPE, 
            freqmin=FILTER_FREQ_MIN, 
            freqmax=FILTER_FREQ_MAX, 
            corners=FILTER_CORNERS
        )
    except Exception as e:
        logging.error(f"Cannot filter the stream: {str(e)}")
        continue
    
    plot_init_filt = utilities.plotStreams(stream,  title=f"Filtered records ({str(FILTER_FREQ_MIN).replace('.', ',')}-{str(FILTER_FREQ_MAX).replace('.', ',')} Hz) - {record_name}")
    figures_pdf.savefig(plot_init_filt)
    plt.close(plot_init_filt)
   
    try:
        stream.detrend(type=DETREND_TYPE)
    except Exception as e:
        logging.error(f"Cannot detrend the stream: {str(e)}")
        continue
    
    plot_ini_filt_det = utilities.plotStreams(stream,  title=f"Filtered ({str(FILTER_FREQ_MIN).replace('.', ',')}-{str(FILTER_FREQ_MAX).replace('.', ',')} Hz) & Detrended (type={DETREND_TYPE}) - {record_name}")
    figures_pdf.savefig(plot_ini_filt_det)
    plt.close(plot_ini_filt_det)

    first_trace = stream.traces[0]
    starttime = first_trace.stats.starttime
    endtime = first_trace.stats.endtime
    
    ps_arrivals = functions.get_record_arrivals(record_name)
    
    if ps_arrivals is None:
        error_message = f"The record '{record_name}' does not have arrivals!"
        logging.error(error_message)
        continue 

    error_message = utilities.validate_arrivals(stream, ps_arrivals)

    if error_message is not None: 
        logging.error(error_message)
        continue

    Parr = ps_arrivals["Parr"]
    Sarr = ps_arrivals["Sarr"]

    plot_arr = utilities.plotStreams(stream,  title=f"Arrivals Selection Parr={str(Parr).replace('.', ',')} & Sarr={str(Sarr).replace('.', ',')}", parr=Parr, sarr=Sarr)
    figures_pdf.savefig(plot_arr)
    plt.close(plot_arr)

    noise_trim_left = Parr - WINDOW_LENGTH - 1
    noise_trim_right = Parr + 1
    signal_trim_left = Sarr - 1
    signal_trim_right = Sarr + WINDOW_LENGTH + 1

    st_noise = stream.copy() # copy for noise stream
    st_signal = stream.copy() # copy for signal stream
   
    try:
        st_noise.trim(starttime=starttime+noise_trim_left, endtime=starttime+noise_trim_right)
        st_signal.trim(starttime=starttime+signal_trim_left, endtime=starttime+signal_trim_right)
    except Exception as e:
        error_message = f"Cannot trim the trace to create a noise and a signal part: {str(e)}"
        logging.error(error_message)
        continue

    plot_noise_trim = utilities.plotStreams(st_noise,  title=f"Trimmed noise between {str(noise_trim_left).replace('.', ',')} and {str(noise_trim_right).replace('.', ',')}")
    plot_signal_trim = utilities.plotStreams(st_signal,  title=f"Trimmed signal between {str(signal_trim_left).replace('.', ',')} and {str(signal_trim_right).replace('.', ',')}")
    figures_pdf.savefig(plot_noise_trim)
    figures_pdf.savefig(plot_signal_trim)
    plt.close(plot_noise_trim)
    plt.close(plot_signal_trim)

    try:
        st_noise.detrend(type=DETREND_TYPE)
        st_signal.detrend(type=DETREND_TYPE)
    except Exception as e:
        error_message = f"Cannot detrend the traces: {str(e)}"
        logging.error(error_message)
        continue

    try:
        st_noise.taper(None, type=TAPER_TYPE, max_length=TAPER_MAX_LENGTH, side=TAPER_SIDE)
        st_signal.taper(None, type=TAPER_TYPE, max_length=TAPER_MAX_LENGTH, side=TAPER_SIDE)
    except Exception as e:
        error_message = f"Cannot taper the noise and/or the signal part: {str(e)}"
        logging.error(error_message)
        continue

    plot_noise_trim_tap = utilities.plotStreams(st_noise,  title=f"Trimmed, detrended and tapered noise")
    plot_signal_trim_tap = utilities.plotStreams(st_signal,  title=f"Trimmed, detrended and tapered signal")
    figures_pdf.savefig(plot_noise_trim_tap)
    figures_pdf.savefig(plot_signal_trim_tap)
    plt.close(plot_noise_trim_tap)
    plt.close(plot_signal_trim_tap)
    
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

        fig, ax = plt.subplots(1, 1)
        ax.set_title(f"FAS & Response Spectra, {record_name}, component: {tr_signal.stats.component}")
        ax.plot(tr_noise_dict["fas_freqs"], tr_noise_dict["fas_amps"], lw=1, color="gray", label=f"noise part")
        ax.plot(tr_signal_dict["fas_freqs"], tr_signal_dict["fas_amps"], lw=1, color="red", label=f"signal part")
        ax.scatter(tr_noise_dict["fas_freqs_interp"], tr_noise_dict["fas_amps_interp"], label=f"Interpolated fas", c="black", zorder=100)
        ax.scatter(tr_signal_dict["fas_freqs_interp"], tr_signal_dict["fas_amps_interp"], label=f"Interpolated fas", c="black", zorder=100)
        ax.plot(1/response_dict["spec"]["Period"], response_dict["spec"]["Pseudo-Velocity"]*0.1/9.81, label="response spectra (Velocity)")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.legend()
        figures_pdf.savefig(fig)
        plt.close(fig)
    
figures_pdf.close()


print("Done...")
logging.info("Done...")
    

    