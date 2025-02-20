from obspy.core import Stream, UTCDateTime, Trace
import pandas as pd
from pathlib import Path
import numpy as np
from obspy.signal.konnoohmachismoothing import konno_ohmachi_smoothing


class StreamHandler(Stream):
    def __init__(self, traces: list | None = None):
        super().__init__(traces=traces)
        self.arrivals = {"p_arr": None, "s_arr": None}

    def set_arrivals(self, all_arrivals: dict[str, dict]):
        record_name = self.get_record_name()
        if record_name not in all_arrivals:
            raise Exception(f"The arrivals of the record {record_name} do not exist!")
        self.arrivals = all_arrivals[record_name]

    @property
    def p_arr(self) -> UTCDateTime:
        return self.arrivals["p_arr"]
    
    @property
    def s_arr(self) -> UTCDateTime:
        return self.arrivals["s_arr"]
    
    @property
    def starttime(self) -> UTCDateTime:
        return self.traces[0].stats.starttime
    
    @property
    def endtime(self) -> UTCDateTime:
        return self.traces[0].stats.endtime
    
    @property
    def duration(self) -> float:
        return float(self.endtime - self.starttime)
    
    @property
    def station(self) -> str:
        return self.traces[0].stats.station
    
    def get_record_name(self) -> str:
        rec_name = f"{self.starttime.date.isoformat()}_{self.starttime.time.isoformat()}_{self.station}"
        return rec_name.replace(":", "").replace("-", "")

    def validate_seismic_file(self) -> str | None:
        if len(self.traces) == 0:
            return "No traces found in the seismic file!"
        for tr in self.traces:
            if len(tr.data) == 0:
                return f"There is an empty trace (component: {tr.stats.channel})"
            elif tr.stats.sampling_rate == 1 or tr.stats.delta == 1:
                return "The sampling rate or the sampling distance (delta) are not set!"
        return None

    @classmethod
    def from_txt(cls, txt_file_path: str | Path):
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
                header = stats.copy()
                header["channel"] = c
                tr = Trace(data=data, header=header)
                traces.append(tr)

            return cls(traces=traces)

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