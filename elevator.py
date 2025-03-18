import json, os, time, sys
sys.path.extend(['.', '..']) # for local imports
from mijiaAPI import mijiaAPI, mijiaDevices, mijiaLogin
from mijiaAPI import get_device_info


from utils import qr_code_login
from const import (
    SWITCH_MODEL_ID,
    DEV_INFO_PATH,
    JSON_FILE_PATH,
    ELEVATOR_DEVICE_ID,
    DEVICES_LIST,
    CREDENTIALS,
    MIJIA_AUTH,
)

class Elevator:
    def __init__(self, credentials: str, auth: str, devices: str, elevator_did: str, dev_info: str, model: str = SWITCH_MODEL_ID): # auth, devices, elevator_did are paths to json files
        # Load the credentials from the json file
        self.credentials = json.loads(open(credentials, 'r', encoding='utf-8').read())
        # Load the authentication details from the json file
        self.auth = json.loads(open(auth, 'r', encoding='utf-8').read())
        # Load the devices from the json file
        self.devices = json.loads(open(devices, 'r', encoding='utf-8').read())
        # Load the elevator device id from the json file
        self.elevator_did = json.loads(open(elevator_did, 'r', encoding='utf-8').read())
        # Load the device information from the json file
        self.dev_info = json.loads(open(dev_info, 'r', encoding='utf-8').read())
        # Create an instance of the mijiaAPI class with the authentication details
        try:
            self.api = mijiaAPI(self.auth)
        except:
            qr_code_login()
            self.auth = json.loads(open(auth, 'r', encoding='utf-8').read())
            self.api = mijiaAPI(self.auth)
        # Set the model to the default value
        self.model = model
    
    def click_floor(self, target_floor: int):
        # Loop through the list of elevators
        for elevator in self.elevator_did:
            # Check if the elevator name contains the target floor
            if elevator['name'] == (str(target_floor) + '楼电梯'):
                # If it does, set the target_did to the elevator's did
                target_did = elevator['did']
                # Break out of the loop
                break
        # Create a new device object with the target_did
        device = mijiaDevices(api=self.api, dev_info=self.dev_info, did=target_did, sleep_time=2)
        # Run the toggle action on the device
        device.run_action('toggle')

    def get_device_details(self):
        # Get device information using the model
        info = get_device_info(self.model)

        # Check if the directory 'dev_info' exists, if not create it
        if not os.path.exists(DEV_INFO_PATH):
            os.mkdir(DEV_INFO_PATH)

        # Open a file in write mode with the model name as the filename
        with open(f'{DEV_INFO_PATH}/{self.model}.json', 'w', encoding='utf-8') as f:
            # Dump the device information into the file
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        # Sleep for 2 seconds
        time.sleep(2)
        
        # Load the device information from the file
        self.dev_info = json.loads(open(f'{DEV_INFO_PATH}/{self.model}.json', 'r', encoding='utf-8').read())
    
    def refresh_device_list(self):
        # Get the list of devices from the API
        devices = self.api.get_devices_list()['list']
        
        # Open the {DEVICES_LIST} file in write mode and write the devices list to it
        with open(f'{JSON_FILE_PATH}/{DEVICES_LIST}', 'w', encoding='utf-8') as f:
            json.dump(devices, f, indent=2, ensure_ascii=False)
        
        # Wait for 2 seconds
        time.sleep(2) 
        
        # Read the {DEVICES_LIST} file and load it into the devices variable
        self.devices = json.loads(open(f'{JSON_FILE_PATH}/{DEVICES_LIST}', 'r', encoding='utf-8').read())
        
    
    def refresh_floor_list(self):
        # Create an empty list to store the elevator device IDs
        elevator_did_list = []

        # Iterate through the devices list
        for device in self.devices:
            # Check if the device model matches the elevator model
            if device['model'] == self.model:
                # Append the device name and device ID to the elevator_did_list
                elevator_did_list.append({'name': device['name'],'did': device['did']})
        
        # Convert the elevator_did_list to a JSON string
        elevator_did_list = json.dumps(list(elevator_did_list), indent=2, ensure_ascii=False)
        # Write the JSON string to a file
        with open(f'{JSON_FILE_PATH}/{ELEVATOR_DEVICE_ID}', 'w', encoding='utf-8') as f:
            f.write(elevator_did_list)
            
        # Load the JSON string from the file and store it in the elevator_did attribute
        self.elevator_did = json.loads(open(f'{JSON_FILE_PATH}/{ELEVATOR_DEVICE_ID}', 'r', encoding='utf-8').read())
        
if __name__ == '__main__':
    model = SWITCH_MODEL_ID
    credentials = f'{JSON_FILE_PATH}/{CREDENTIALS}'
    auth = f'{JSON_FILE_PATH}/{MIJIA_AUTH}'
    devices = f'{JSON_FILE_PATH}/{DEVICES_LIST}'
    elevator_did = f'{JSON_FILE_PATH}/{ELEVATOR_DEVICE_ID}'
    dev_info = f'{DEV_INFO_PATH}/{model}.json'
        
    elevator = Elevator(credentials=credentials, auth=auth, devices=devices, elevator_did=elevator_did, dev_info=dev_info)
    print(elevator.model)
    elevator.refresh_device_list()
    # time.sleep(1)
    elevator.refresh_floor_list()
    time.sleep(1)
    # elevator.click_floor(2)