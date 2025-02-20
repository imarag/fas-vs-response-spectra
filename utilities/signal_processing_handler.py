from dataclasses import dataclass
from obspy.core import Stream, Trace
from typing import Literal
import numpy as np
from obspy.signal.konnoohmachismoothing import konno_ohmachi_smoothing

@dataclass
class SignalProcessingHandler:

    @staticmethod
    def filter_trace(tr: Trace, freqmin: float | None, freqmax: float | None) -> Trace :
        tr_copy = tr.copy()
        
        # check if the minimum and maximum filter frequencies are within the waveform duration limits
        duration = tr.stats.endtime - tr.stats.starttime 
        if (freqmin is not None and freqmin < 0) or (freqmax is not None and freqmax > duration):
            raise ValueError("The minimum frequency cannot be negative and the maximum cannot be greater than the length of the waveform")

        if freqmin is not None and freqmax is None:
            tr_copy.filter("highpass", freq=float(freqmin))
        elif freqmin is None and freqmax is not None:
            tr_copy.filter("lowpass", freq=float(freqmax))
        elif freqmin is not None and freqmax is not None:
            tr_copy.filter("bandpass", freqmin=float(freqmin), freqmax=float(freqmax))
        return tr_copy

    @staticmethod
    def trim_trace(tr: Trace, left_value: float, right_value: float) -> Trace :
        tr_copy = tr.copy()
        starttime = tr_copy.stats.starttime

        # check if the left and right trim limits are within the waveform duration limits
        duration = tr.stats.endtime - tr.stats.starttime 
        if (left_value is not None and left_value < 0) or (right_value is not None and right_value > duration):
            raise ValueError("The left and right trim values should be within the waveform duration limits")

       
        tr_copy.trim(
            starttime=starttime + left_value, 
            endtime=starttime + right_value
        )
        return tr_copy

    @staticmethod
    def taper_trace(tr: Trace, 
              max_percentage: float | None = None, 
              side: Literal["left", "right", "both"] = "both",
              type: str = "parzen",
              max_length: float | None = None
              ) -> Trace :
        tr_copy = tr.copy()
       
        tr_copy.taper(
            max_percentage, 
            side=side, 
            type=type, 
            max_length=max_length
        )
        return tr_copy

    @staticmethod
    def detrend_trace(tr: Trace, type: Literal["simple", "linear", "constant"] = "simple") -> Trace :
        tr_copy = tr.copy()
        tr_copy.detrend(type)

        return tr_copy


    # Methods for handling Stream objects
    @staticmethod
    def filter_stream(st: Stream, freqmin: float | None, freqmax: float | None) -> Stream :
        st_copy = st.copy()

        # check if the minimum and maximum filter frequencies are within the waveform duration limits
        tr = st_copy.traces[0]
        duration = tr.stats.endtime - tr.stats.starttime 
        if (freqmin is not None and freqmin < 0) or (freqmax is not None and freqmax > duration):
            raise ValueError("The minimum frequency cannot be negative and the maximum cannot be greater than the length of the waveform")


        if freqmin is not None and freqmax is None:
            st_copy.filter("highpass", freq=float(freqmin))
        elif freqmin is None and freqmax is not None:
            st_copy.filter("lowpass", freq=float(freqmax))
        elif freqmin is not None and freqmax is not None:
            st_copy.filter("bandpass", freqmin=float(freqmin), freqmax=float(freqmax))
        
        return st_copy

    @staticmethod
    def trim_stream(st: Stream, left_value: float, right_value: float) -> Stream :
        st_copy = st.copy()

        # check if the left and right trim limits are within the waveform duration limits
        tr = st_copy.traces[0]
        duration = tr.stats.endtime - tr.stats.starttime 
        if (left_value is not None and left_value < 0) or (right_value is not None and right_value > duration):
            raise ValueError("The left and right trim values should be within the waveform duration limits")
        
        for tr in st_copy:
            starttime = tr.stats.starttime
            tr.trim(
                starttime=starttime + left_value,
                endtime=starttime + right_value
            )
        return st_copy

    @staticmethod
    def taper_stream(st: Stream, 
               max_percentage: float | None = None, 
               side: Literal["left", "right", "both"] = "both",
               type: str = "parzen",
               max_length: float | None = None
               ) -> Stream :
        st_copy = st.copy()
        st_copy.taper(
            max_percentage, 
            side=side, 
            type=type, 
            max_length=max_length
        )
        return st_copy

    @staticmethod
    def detrend_stream(st: Stream, type: Literal["simple", "linear", "constant"] = "simple") -> Stream :
        st_copy = st.copy()

        st_copy.detrend(type)
        return st_copy

    @staticmethod
    def compute_fourier(tr: Trace) -> tuple[np.ndarray, np.ndarray]:

        # trace stats
        tr_stats = tr.stats

        # compute necessary fourier variables
        sl = int(tr_stats.npts / 2)
        fnyq = tr_stats.sampling_rate / 2

        freq = np.linspace(0, fnyq, sl)
        tr_fft = np.fft.fft(tr.data[:tr_stats.npts])
        tr_fft_abs = tr_stats.delta * np.abs(tr_fft)[0:sl]
        
        return freq, tr_fft_abs
    
    @staticmethod
    def apply_konno_omachi_filtering(freqs: np.ndarray, spectra: np.ndarray, bandwidth: int = 40) -> np.ndarray:
        filtered_spectra = konno_ohmachi_smoothing(spectra, freqs, bandwidth=bandwidth, normalize=True)
        return np.array(filtered_spectra)