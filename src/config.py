from pathlib import Path 
from matplotlib.backends.backend_pdf import PdfPages
import logging
from enum import Enum 
import os

class AppRoutes(Enum):
    ROOT_DIR_PATH = Path(__file__).parent.parent
    DATA_FOLDER_PATH = ROOT_DIR_PATH / "data"

class AppConfig(Enum):
    LOG_FILE_PATH = "app.log"
    PLOTS_PDF = PdfPages('figures.pdf')

class AppParameters(Enum):
    DETREND_TYPE = "simple"
    TAPER_SIDE = "both"
    TAPER_TYPE = "parzen"
    TAPER_MAX_LENGTH = 1
    FILTER_TYPE = "bandpass"
    FILTER_FREQ_MIN = 0.1
    FILTER_FREQ_MAX = 100
    FILTER_CORNERS = 4
    KONNO_OMACHI_BANDWIDTH = 50
    WINDOW_LENGTH = 5
    FOURIER_MIN_FREQ = 0.2 
    FOURIER_MAX_FREQ = 30
    FOURIER_TOTAL_FREQS = 30
    SIGNAL_TO_NOISE = 5
    RESPONSE_SPECTRA_MIN_PERIOD = 0.01
    RESPONSE_SPECTRA_MAX_PERIOD = 20
    RESPONSE_SPECTRA_TOTAL_PERIODS = 300
    RESPONSE_SPECTRA_DUMPING = 0.05

def setup_environment():
    if not os.path.exists(AppRoutes.DATA_FOLDER_PATH.value):
        raise Exception("Folder 'data' is not found!")
    
    if len(os.listdir(AppRoutes.DATA_FOLDER_PATH.value)) == 0:
        raise Exception("The folder 'data' is empty!")

    logging.basicConfig(
        filename=AppConfig.LOG_FILE_PATH.value, 
        filemode='a',       
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'  
    )

def handle_error(message: str) -> None:
    logging.error(message)

def handle_info(message: str) -> None:
    print(message)
    logging.info(message)

def cleanup_resources():
    AppConfig.PLOTS_PDF.value.close()
    handle_info(f"Done...")