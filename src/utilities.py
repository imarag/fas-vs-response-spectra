from obspy.core import Stream
from config import *
import matplotlib.pyplot as plt

def get_record_name(stream: Stream) -> str:
    first_trace = stream.traces[0]
    starttime = first_trace.stats.starttime
    station = first_trace.stats.station

    if not station:
        station = "STATION"

    rec_name = f"{starttime.date.isoformat()}_{starttime.time.isoformat()}_{station}"
    
    return rec_name.replace(":", "").replace("-", "")

def validate_stream(st: Stream) -> str | None:
    if len(st.traces) == 0:
        error_message = "No traces found in the seismic file!"
        return error_message
    
    for tr in st.traces:
        if len(tr.data) == 0:
            error_message = f"There is an empty trace (component: {tr.stats.component})"
            return error_message 
        elif tr.stats.sampling_rate == 1 or tr.stats.delta == 1:
            error_message = "The sampling rate or the sampling distance (delta) are not set!"
            return error_message 


def validate_arrivals(stream: Stream, ps_arrivals: dict) -> str | None:
    record_name = get_record_name(stream)
    first_trace = stream.traces[0]
    duration = first_trace.stats.endtime - first_trace.stats.starttime

    window_length = AppParameters.WINDOW_LENGTH.value

    if "Parr" not in ps_arrivals:
        error_message = f"The record '{record_name}' does not have P wave arrival"
        return error_message
    
    if "Sarr" not in ps_arrivals:
        error_message = f"The record '{record_name}' does not have S wave arrival"
        return error_message
    
    Parr = ps_arrivals["Parr"]
    Sarr = ps_arrivals["Sarr"]
    
    if Parr is None:
        error_message = f"The record '{record_name}' does not have P wave arrival"
        return error_message

    if Sarr is None:
        error_message = f"The record name '{record_name}' does not have S wave arrival"
        return error_message
    
    # the P arrival cannot be greater or equal to the S arrival
    if  Parr >= Sarr:
        error_message = f"The P wave arrival cannot be greater or equal to the S arrival"
        return error_message

    # the P arrival must be >= WINDOW_LENGTH+1 to be able to apply the trim
    # trim: Parr - window - 1 to Parr + 1
    if Parr < (window_length+1):
        error_message = f"The P wave arrival value ({Parr}) is too small for the specified window length ({window_length}). It must be greater or equal to {window_length+1}"
        return error_message
    
    # the S arrival must be <= duration - (WINDOW_LENGTH + 1) to apply the trim
    # trim: Sarr - 1 to Sarr + window + 1
    if Sarr > duration-(window_length+1):
        error_message = f"The S wave arrival value ({Sarr}) is too big for the specified window length ({window_length}). It must be less than or equal to {duration-window_length-1}"
        return error_message
    
def plot_FAS_response_spectra(tr_noise_dict: dict, tr_signal_dict: dict, response_dict: dict, component: str):
    fig, ax = plt.subplots(1, 1)
    ax.set_title(f"FAS & Response Spectra, component: {component}")
    ax.plot(tr_noise_dict["fas_freqs"], tr_noise_dict["fas_amps"], lw=1, color="gray", label=f"noise part")
    ax.plot(tr_signal_dict["fas_freqs"], tr_signal_dict["fas_amps"], lw=1, color="red", label=f"signal part")
    ax.scatter(tr_noise_dict["fas_freqs_interp"], tr_noise_dict["fas_amps_interp"], label=f"Interpolated fas", c="black", zorder=100)
    ax.scatter(tr_signal_dict["fas_freqs_interp"], tr_signal_dict["fas_amps_interp"], label=f"Interpolated fas", c="black", zorder=100)
    ax.plot(1/response_dict["spec"]["Period"], response_dict["spec"]["Pseudo-Velocity"]*0.1/9.81, label="response spectra (Velocity)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend()
    AppConfig.PLOTS_PDF.value.savefig(fig)
    plt.close(fig)

def plot_stream(stream, title="", parr=None, sarr=None) -> None:
    record_name = get_record_name(stream)
    fig, ax = plt.subplots(3, 1)
    fig.suptitle(title + " - " + record_name, fontsize=10)
    for i in range(3):
        tr = stream.traces[i]
        ax[i].plot(tr.times(), tr.data, lw=1, label=f"component: {tr.stats.component}")

        if any([parr, sarr]):
            ax[i].axvline(x=parr, label="Parr", color="black", ls="--")
            ax[i].axvline(x=sarr, label="Sarr", color="red", ls="--")
        ax[i].legend(loc="upper right")
    
    AppConfig.PLOTS_PDF.value.savefig(fig)
    plt.close(fig)