from pathlib import Path 
from obspy.core import UTCDateTime, Trace, Stream
import pandas as pd
from utilities.stream_handler import StreamHandler

data_folder_path = Path(__file__).parent / "data"
mseed_folder_path = Path(__file__).parent / "mseed_data"

if not mseed_folder_path.exists():
    mseed_folder_path.mkdir()

for seismic_file in data_folder_path.iterdir():
    
    with open(seismic_file, "r") as file:
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
            header["channel"] = c
            tr = Trace(data=data, header=header)
            traces.append(tr)
        
        st = Stream(traces = traces)

        record_name = StreamHandler(st).get_record_name()
        st.write(mseed_folder_path / str(record_name + ".mseed"))
