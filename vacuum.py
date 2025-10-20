import asyncio, json, requests

from roborock import HomeDataProduct, DeviceData, RoborockCommand, UserData
from roborock.version_1_apis import RoborockMqttClientV1, RoborockLocalClientV1
from roborock.web_api import RoborockApiClient

from const import (
    VACUUM_ENTITY_ID,
    HOME_ASSISTENT_URL,
    HOME_ASSISTENT_PORT,
    HOME_ASSISTANT_API_KEY,
    JSON_FILE_PATH,
    FLOOR_MINIMUM,
    FLOOR_MAXIMUM,
    DOCK_FLOOR,
    ROBOROCK_AUTH,
    ROOMS_DATA,
    FLOOR_MAP_REFERENCE,
)

floor_map_reference = {
    "3": 2,
    "2": 1,
    "1": 0,
}

class Vacuum():
    def __init__(self, credentials: str, auth: str, positions: str, rooms: str, entity_id: str = VACUUM_ENTITY_ID):
        # Load the credentials, auth, and positions from the given files
        self.credentials = json.loads(open(credentials, 'r', encoding='utf-8').read())
        self.auth = json.loads(open(auth, 'r', encoding='utf-8').read())
        self.user_data = UserData.from_dict(json.loads(open(auth, 'r', encoding='utf-8').read()))
        self.position_data = json.loads(open(positions, 'r', encoding='utf-8').read())
        self.rooms = json.loads(open(rooms, 'r', encoding='utf-8').read())
        self.api = None
        self.home_data = None
        self.device_data = None
        self.map_floor = DOCK_FLOOR
        self.entity_id = entity_id
        self.is_available = True # Flag to check if the vacuum is available
    
    def get_availability(self) -> bool:
        # Check if the vacuum is available
        return self.is_available
    
    def get_vacuum_status(self) -> str: 
        # Get the vacuum status from the Home Assistant API
        url = f"{HOME_ASSISTENT_URL}:{HOME_ASSISTENT_PORT}/api/states/{self.entity_id}" # Create the URL for the Home Assistant API
        headers = {
            "Authorization": f"Bearer {HOME_ASSISTANT_API_KEY}", # Set the authorization header with the Home Assistant API key
            "content-type": "application/json",
        }
        response = requests.get(url, headers=headers) # Make a GET request to the Home Assistant API
        response_json = json.loads(response.text) # Load the response as a JSON object
        return response_json['state'] # usually idle, cleaning, docked, paused, etc. Return the vacuum status from the JSON object
    
    
    async def refresh_vacuum_state(self, state: str): # refresh the state of the vacuum using Home Assistant API
        # 1. IDLE -> In position
        # 2. CLEANING -> On the way to the point
        # 3. RETURNING
        while True:
            current_state = self.get_vacuum_status().lower()
            # print(current_state)

            if state.find(current_state) != -1 or current_state.find(state) != -1: # In Position
                break 

            await asyncio.sleep(5)
    
    async def login(self):
        # Login to the Roborock API
        self.auth = json.loads(open(f"{JSON_FILE_PATH}/{ROBOROCK_AUTH}", 'r', encoding='utf-8').read()) # Need Imporvement on hard coding
        self.user_data = UserData.from_dict(self.auth)
        try:
            # Try the cache login information first
            self.home_data = await RoborockApiClient(username=self.credentials['email']).get_home_data_v2(user_data = self.user_data)
        except:
            await self.credentials_login()
            self.auth = json.loads(open(f"{JSON_FILE_PATH}/{ROBOROCK_AUTH}", 'r', encoding='utf-8').read()) # Need Imporvement on hard coding
            self.user_data = UserData.from_dict(self.auth)
            self.home_data = await RoborockApiClient(username=self.credentials['email']).get_home_data_v2(user_data = self.user_data)
        
        # Get the device you want
        device = self.home_data.devices[0]
        # Get product ids:
        product_info: dict[str, HomeDataProduct] = {
                product.id: product for product in self.home_data.products
            }
        # Create the Mqtt(aka cloud required) Client
        self.device_data = DeviceData(device, product_info[device.product_id].model)
        mqtt_client = RoborockMqttClientV1(self.user_data, self.device_data)
        networking = await mqtt_client.get_networking()
        local_device_data = DeviceData(device, product_info[device.product_id].model, networking.ip)
        self.api = RoborockLocalClientV1(local_device_data)
        
    async def credentials_login(self):
        # Login to the Roborock API using the credentials
        web_api = RoborockApiClient(username=self.credentials['email'])
        # Login via your password
        user_data = await web_api.pass_login(password=str(self.credentials['password']).lower())
        
        with open(f'{JSON_FILE_PATH}/{ROBOROCK_AUTH}', 'w') as f:
            json.dump(user_data.as_dict(), f, indent=2)

    async def refresh_rooms(self):
        rooms_data_raw = await self.api.get_room_mapping()
        with open(f'{JSON_FILE_PATH}/rooms.json', 'w') as f:
            f.write(json.dumps(rooms_data_raw, default=lambda o: o.__dict__, indent=2, ensure_ascii=False))

    async def move_to_recognition_position(self):
        # Move the vacuum to the recognition point in case the elevator door is closed
        x_coord = self.position_data[f'{self.map_floor}']['recognition']['x']
        y_coord = self.position_data[f'{self.map_floor}']['recognition']['y']
        await self.send(RoborockCommand.APP_GOTO_TARGET, [x_coord, y_coord])

    async def move_to_transition_point(self): 
        # Move the vacuum to the transition point
        x_coord = self.position_data[f'{self.map_floor}']['waiting']['x']
        y_coord = self.position_data[f'{self.map_floor}']['waiting']['y']
        await self.send(RoborockCommand.APP_GOTO_TARGET, [x_coord, y_coord])
    
    async def exit_elevator(self, target_floor: int):
        # Exit the elevator using the transition point of the former floor
        # Change the map selection to the current floor
        if target_floor == -2:
            return # The function for B2 is still developing

        x_coord = self.position_data[f'{self.map_floor}']['recognition']['x']
        y_coord = self.position_data[f'{self.map_floor}']['recognition']['y']
        
        try: 
            await self.send(RoborockCommand.APP_GOTO_TARGET, [x_coord, y_coord])
        except:
            print("Goto Error")
            await asyncio.sleep(2)
        await asyncio.sleep(15)
        await self.refresh_vacuum_state('idle, paused')
        try:
            await asyncio.sleep(4)
            await self.api.load_multi_map(FLOOR_MAP_REFERENCE[str(target_floor)])
            await asyncio.sleep(2)
            self.map_floor = target_floor
        except Exception as e:
            print("Map change error " + str(e))
            await asyncio.sleep(2)

        # Used to be while - break
    
    async def enter_elevator(self):
        # Enter the elevator
        x_coord = self.position_data[f'{self.map_floor}']['elevator']['x']
        y_coord = self.position_data[f'{self.map_floor}']['elevator']['y']
        await self.send(RoborockCommand.APP_GOTO_TARGET, [x_coord, y_coord])
    
    async def send(self, command: RoborockCommand, params: dict):
        # Send a command to the vacuum
        await self.api.send_command(command, params=params)
        
    async def stop(self):
        # Stop the vacuum
        await self.send(RoborockCommand.APP_STOP, params=[])
        self.is_available = True
    
    def get_map_floor(self):
        # Get the current map floor
        return self.map_floor
