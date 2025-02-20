from pathlib import Path 
import logging
import os 
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

DATA_FOLDER_PATH = Path(__file__).parent / "data"
IMAGES_FOLDER_PATH = Path(__file__).parent / "images"

if not os.path.exists(DATA_FOLDER_PATH):
    raise Exception("Folder 'data' is not found!")

if not os.listdir(DATA_FOLDER_PATH):
    raise Exception("Folder 'data' is empty!")

if not os.path.exists(IMAGES_FOLDER_PATH):
    os.mkdir(IMAGES_FOLDER_PATH)

# set the logging file name
LOGGING_FILE = "app.log"

# if it exists remove it
if os.path.exists(LOGGING_FILE):
    os.remove(LOGGING_FILE)

# set the configuration to show the logs in the file
logging.basicConfig(
    filename=LOGGING_FILE, 
    filemode='a',       
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'  
)

# set the various parameters that we use in the code
DETREND_TYPE = "simple"

TAPER_SIDE = "both"
TAPER_TYPE = "parzen"
TAPER_MAX_LENGTH = 1

FILTER_TYPE = "bandpass"
FILTER_FREQ_MIN = 0.05
FILTER_FREQ_MAX = 100
FILTER_CORNERS = 4

KONNO_OMACHI_BANDWIDTH = 50
WINDOW_LENGTH = 5

FOURIER_MIN_FREQ = 0.2 
FOURIER_MAX_FREQ = 30
FOURIER_TOTAL_FREQS = 30
SIGNAL_TO_NOISE = 5

