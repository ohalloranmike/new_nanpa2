import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = BASE_DIR / "static"
    NANPA_DIR = STATIC_DIR / "NANPA"
    TEMPLATE_DIR = BASE_DIR / "templates"
    DB_PATH = NANPA_DIR / "pn.db"

    HOST = os.environ.get("NANPA_HOST", "127.0.0.1")
    PORT = int(os.environ.get("NANPA_PORT", "8002"))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")

    REFRESH_ON_START = os.environ.get("NANPA_REFRESH_ON_START", "0") == "1"
    DB_MAX_AGE_DAYS = int(os.environ.get("NANPA_DB_MAX_AGE_DAYS", "7"))
    REQUESTS_VERIFY = os.environ.get("NANPA_REQUESTS_VERIFY", "0") == "1"

    NANPA_NPA_URL = "https://reports.nanpa.com/public/npa_report.csv"
    NANPA_OC_ZIP_URL = "https://reports.nanpa.com/public/CoCodeAssignment_Utilized_AllStates_Public.zip"
    CNAC_OC_ZIP_URL = "https://www.cnac.ca/data/COCodeStatus_ALL.zip"

    USAC_MAP_URL = "/USACMaps/"
    STATE_MAP_URL = "/USStateMaps/"
    TERRITORY_MAP_URL = "/USTerritoryACMaps/"
    CANADA_MAP_URL = "/CanadaACMaps/"
    COUNTRY_MAP_URL = "/CountryACMaps/"
