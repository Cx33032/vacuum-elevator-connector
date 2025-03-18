from mijiaAPI import mijiaLogin
import json, os, sys, time
sys.path.extend(['.', '..'])

from vacuum import Vacuum

from const import (
    MIJIA_AUTH,
    JSON_FILE_PATH,
    DEV_INFO_PATH,
)

def check_path_exist():
    if not os.path.exists(JSON_FILE_PATH):
        os.mkdir(JSON_FILE_PATH)
    if not os.path.exists(DEV_INFO_PATH):
        os.mkdir(DEV_INFO_PATH)

def qr_code_login():
    api = mijiaLogin()
    auth = api.QRlogin()
    with open(f'{JSON_FILE_PATH}/{MIJIA_AUTH}', 'w') as f:
        json.dump(auth, f, indent=2)

def refresh_vacuum_state(vacuum: Vacuum): # refresh the state of the vacuum using Home Assistant API
    # IDLE -> In position
    # CLEANING -> On the way to the point
    while True:
        current_state = vacuum.get_vacuum_status()
        if current_state == 'idle': # In Position
            break
        else:
            time.sleep(5)
