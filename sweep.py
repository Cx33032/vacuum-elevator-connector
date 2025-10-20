from const import DOCK_FLOOR, MOP_WASHING_TIME, DUST_COLLECTING_TIME
from utils import refresh_vacuum_state
from vacuum import Vacuum
from elevator import Elevator

from datetime import datetime
from roborock import RoborockCommand

import asyncio, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def goto_level(
    vacuum: Vacuum, 
    elevator: Elevator, 
    current_level: int, 
    target_level: int
):
    
    if current_level == target_level:
        return
    
    # current_time = time.strftime('%H:%M:%S', time.localtime())
    logger.info(f'{datetime.now()} - Currently at Level {current_level}. On the way to Level {target_level}')
    # print(f'{current_time} - Currently at Level {current_level}. On the way to Level {target_level}')
    # Waiting for the elevator
    await vacuum.send(RoborockCommand.APP_STOP, params=[])
    await asyncio.sleep(5)
    elevator.click_floor(current_level)
    await vacuum.move_to_recognition_position()
    await asyncio.sleep(30)
    await refresh_vacuum_state(vacuum, 'idle, paused')
    await vacuum.move_to_transition_point()
    await asyncio.sleep(30)
    await refresh_vacuum_state(vacuum, 'idle, paused')
    await asyncio.sleep(15)
    
    # Enter the elevator
    for _ in range(2):
        await vacuum.enter_elevator()
        await asyncio.sleep(25)
        await refresh_vacuum_state(vacuum, 'idle, paused')
        await asyncio.sleep(10)
    
    
    elevator.click_floor(current_level)

    # Move to the destination floor
    elevator.click_floor(target_level)
    await asyncio.sleep(10 * abs(current_level - target_level) + 30) # Need 20 seconds in elevator operation
    await vacuum.exit_elevator(target_level)
    
    await asyncio.sleep(2)
    # refresh_vacuum_state(vacuum)
    elevator.click_floor(target_level)
    logger.info(f'{datetime.now()} - Arrived at Level {target_level}')

async def clean_room(
    vacuum: Vacuum, 
    floor: int, 
    segment_id: int
):
    
    await vacuum.send(RoborockCommand.APP_STOP, params=[])
    await asyncio.sleep(2)

    try:
        await vacuum.send(RoborockCommand.APP_SEGMENT_CLEAN, params=[segment_id])
    except:
        logger.error(f"{datetime.now()} - App Start Error")

    logger.info(f'{datetime.now()} - Start to clean Level {floor}, Room {segment_id}')

async def return_to_base(
    vacuum: Vacuum,
    elevator: Elevator,
    current_floor: int
):
    await goto_level(vacuum=vacuum, elevator=elevator, current_level=current_floor, target_level=DOCK_FLOOR)

    # Back to charge
    try:
        logger.info(f'{datetime.now()} - Returning to the dock')
        await vacuum.send(RoborockCommand.APP_CHARGE, params=[])
        await refresh_vacuum_state(vacuum, 'docked')

        logger.info(f'{datetime.now()} - Satrt to wash the mop')
        await vacuum.send(RoborockCommand.APP_START_WASH, params=[])
        await asyncio.sleep(MOP_WASHING_TIME)
        await vacuum.send(RoborockCommand.APP_STOP_WASH, params=[])
        await asyncio.sleep(3)

        logger.info(f'{datetime.now()} - Start to collect the dust')
        await vacuum.send(RoborockCommand.APP_START_COLLECT_DUST, params=[])
        await asyncio.sleep(DUST_COLLECTING_TIME)
        await vacuum.send(RoborockCommand.APP_STOP_COLLECT_DUST, params=[])
    except:
        # current_time = time.strftime('%H:%M:%S', time.localtime())
        # print(f"{datetime.now()} - Return Error")
        logger.error(f'{datetime.now()} - Return Error')
    current_floor = DOCK_FLOOR

async def sweep_main(
    vacuum: Vacuum,
    elevator: Elevator,
    floor: int,
    claen_segment_id_list: list
):
    # current_time = time.strftime('%H:%M:%S', time.localtime())
    # print(f'{current_time} - Logging in...')
    logger.info(f"{datetime.now()} - Starting to clean")
    await vacuum.login()
    await asyncio.sleep(2)
    
    elevator.click_floor(DOCK_FLOOR)
    await asyncio.sleep(1)
    elevator.click_floor(DOCK_FLOOR)
    
    logger.info(f'{datetime.now()} - Washing the mop')
    await vacuum.send(RoborockCommand.APP_START_WASH, params=[])
    await asyncio.sleep(MOP_WASHING_TIME)
    await vacuum.send(RoborockCommand.APP_STOP_WASH, params=[])
    
    
    for ids in claen_segment_id_list:
        await goto_level(vacuum=vacuum, elevator=elevator, current_level=DOCK_FLOOR, target_level=floor)
        for id in ids:
            await clean_room(vacuum=vacuum, floor=floor, segment_id=id)
            await refresh_vacuum_state(vacuum, 'returning')
            try:
                await vacuum.api.send_command(RoborockCommand.APP_STOP, params=[]) 
                # Very IMPORTANT, otherwise, the robot can not change the map
                await asyncio.sleep(3)
            except:
                logger.error(f'{datetime.now()} - App stop error')
                # print(f"{datetime.now()} - App stop error")
        await return_to_base(vacuum=vacuum, elevator=elevator, current_floor=floor)