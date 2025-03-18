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
)

floor_map_reference = {
    "3": 0,
    "2": 1,
}

class Vacuum():
    def __init__(self, credentials: str, auth: str, positions: str, entity_id: str = VACUUM_ENTITY_ID):
        # Load the credentials, auth, and positions from the given files
        self.credentials = json.loads(open(credentials, 'r', encoding='utf-8').read())
        self.auth = json.loads(open(auth, 'r', encoding='utf-8').read())
        self.user_data = UserData.from_dict(json.loads(open(auth, 'r', encoding='utf-8').read()))
        self.position_data = json.loads(open(positions, 'r', encoding='utf-8').read())
        self.api = None
        self.home_data = None
        self.device_data = None
        self.map_floor = 3
        self.entity_id = entity_id
    
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

        if target_floor == DOCK_FLOOR:
            x_coord = self.position_data[f'{self.map_floor}']['dock']['x']
            y_coord = self.position_data[f'{self.map_floor}']['dock']['y']
        elif target_floor <= FLOOR_MAXIMUM and target_floor >= FLOOR_MINIMUM:
            x_coord = self.position_data[f'{self.map_floor}']['waiting']['x']
            y_coord = self.position_data[f'{self.map_floor}']['waiting']['y']
        else:
            raise ValueError('Floor value out of bound')

        await self.send(RoborockCommand.APP_GOTO_TARGET, [x_coord, y_coord])
        try:
            await self.send(RoborockCommand.LOAD_MULTI_MAP, [floor_map_reference[str(target_floor)]]) # Need to fix
            self.map_floor = target_floor
        except:
            pass
    
    async def enter_elevator(self):
        # Enter the elevator
        x_coord = self.position_data[f'{self.map_floor}']['elevator']['x']
        y_coord = self.position_data[f'{self.map_floor}']['elevator']['y']
        await self.send(RoborockCommand.APP_GOTO_TARGET, [x_coord, y_coord])
    
    async def send(self, command: RoborockCommand, params: dict):
        # Send a command to the vacuum
        await self.api.send_command(command, params=params)
    