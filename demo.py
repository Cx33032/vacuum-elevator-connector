from const import *
from utils import check_path_exist, refresh_vacuum_state
from vacuum import Vacuum
from elevator import Elevator

from roborock import RoborockCommand

import requests, asyncio

model = SWITCH_MODEL_ID
entity_id = VACUUM_ENTITY_ID

credentials = f'{JSON_FILE_PATH}/{CREDENTIALS}'
mijia_auth = f'{JSON_FILE_PATH}/{MIJIA_AUTH}'
roborock_auth = f'{JSON_FILE_PATH}/{ROBOROCK_AUTH}'

mijia_devices = f'{JSON_FILE_PATH}/{DEVICES_LIST}'
elevator_did = f'{JSON_FILE_PATH}/{ELEVATOR_DEVICE_ID}'
dev_info = f'{DEV_INFO_PATH}/{model}.json'

vacuum_position_list = f'{JSON_FILE_PATH}/{POSITION_DATA}'

vacuum = Vacuum(credentials=credentials, auth=roborock_auth, positions=vacuum_position_list, entity_id=entity_id)
elevator = Elevator(credentials=credentials, auth=mijia_auth, devices=mijia_devices, elevator_did=elevator_did, dev_info=dev_info, model=model)

current_floor = DOCK_FLOOR

async def return_to_charge():
    print(f'Currently at Level {current_floor}. On the way to charge')

    # Elevator moves to the floor vacuum located and the vacuum moves to the waiting position
    elevator.click_floor(current_floor)
    await vacuum.move_to_transition_point()
    await asyncio.sleep(30)

    # Vacuum enter the elevator and refresh to get the state to check is the vacuum in position
    await vacuum.enter_elevator()
    refresh_vacuum_state(vacuum)
    elevator.click_floor(current_floor)

    # Elevator moves to the floor where the dock is located and the vacuum leaves the elevator
    elevator.click_floor(DOCK_FLOOR)
    await asyncio.sleep(10 * abs(DOCK_FLOOR - current_floor) + 15)
    await vacuum.exit_elevator(DOCK_FLOOR)
    refresh_vacuum_state(vacuum)
    elevator.click_floor(DOCK_FLOOR)

    # Back to charge
    try:
        vacuum.send(RoborockCommand.APP_CHARGE)
    except:
        pass
    current_floor = DOCK_FLOOR

async def clean_floor(target_floor: int):
    # print(f'Currently at Level {current_floor}. On the way to Level {target_floor}')
    elevator.click_floor(DOCK_FLOOR)
    await vacuum.move_to_transition_point()
    await asyncio.sleep(30)

    await vacuum.enter_elevator()
    refresh_vacuum_state(vacuum)
    elevator.click_floor(DOCK_FLOOR)

    elevator.click_floor(target_floor)
    await asyncio.sleep(10 * abs(DOCK_FLOOR - target_floor) + 15)
    await vacuum.exit_elevator(target_floor)
    
    refresh_vacuum_state(vacuum)
    elevator.click_floor(target_floor)
    try:
        await vacuum.send(RoborockCommand.APP_START)
    except:
        pass

    # print(f'Start to clean Level {target_floor}')
    # current_floor = target_floor

async def demo_main():
    mode = 'clean'
    if mode == 'clean':
        await clean_floor(2)
    else:
        await return_to_charge()

async def print_status():
    while True:
        print(vacuum.get_vacuum_status())
        await asyncio.sleep(10)

async def main():
    print('Logging in...')
    await vacuum.login()
    await asyncio.sleep(2)
    await asyncio.gather(demo_main(), print_status())

if __name__ == '__main__':
    check_path_exist()
    elevator.refresh_device_list()
    elevator.refresh_floor_list()

    asyncio.run(main())