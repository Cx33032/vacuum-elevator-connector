import gradio as gr
import json
import ast
import asyncio
import time
import threading

from const import *
from vacuum import Vacuum
from elevator import Elevator
from gradio_mijia_login import GradioMijiaLogin

from sweep import sweep_main, goto_level, clean_room, return_to_base

from roborock import RoborockCommand

model = SWITCH_MODEL_ID
entity_id = VACUUM_ENTITY_ID

credentials = f'{JSON_FILE_PATH}/{CREDENTIALS}'
mijia_auth = f'{JSON_FILE_PATH}/{MIJIA_AUTH}'
roborock_auth = f'{JSON_FILE_PATH}/{ROBOROCK_AUTH}'

mijia_devices = f'{JSON_FILE_PATH}/{DEVICES_LIST}'
elevator_did = f'{JSON_FILE_PATH}/{ELEVATOR_DEVICE_ID}'
dev_info = f'{DEV_INFO_PATH}/{model}.json'
rooms = f'{JSON_FILE_PATH}/{ROOMS_DATA}'
levels_path = f'{JSON_FILE_PATH}/{LEVELS_DATA_PATH}/'

vacuum_position_list = f'{JSON_FILE_PATH}/{POSITION_DATA}'

vacuum = Vacuum(credentials=credentials, auth=roborock_auth, positions=vacuum_position_list, rooms=rooms, entity_id=entity_id)
elevator = Elevator(credentials=credentials, auth=mijia_auth, devices=mijia_devices, elevator_did=elevator_did, dev_info=dev_info, model=model)

qr_login = GradioMijiaLogin()
ret_data = None

def update_checkboxes(choice):
    if choice == "L2":
        return gr.update(choices=["卧室", "标间（阳台）", "标间", "走廊", "储物间", "卫生间"], value=[]) # 5, 1, 2, 6, 3, (4, 7, 8)
    elif choice == "L3":
        return gr.update(choices=["书房", "主卧", "衣帽间", "洗衣房", "卫生间"], value=[]) # 2, 1, 5, 3, 4
    elif choice == "B1":
        return gr.update(choices=[], value=[])

def selected_rooms(level_choice, rooms_checkbox):
    level_file = f"{levels_path}{level_choice}.json"
    rooms_json = json.loads(open(level_file, 'r', encoding='utf-8').read())
    segment_ids_list = []
    
    for selection in rooms_checkbox:
        room_ids = rooms_json[f'{selection}']
        for room_id in room_ids:
            segment_ids_list.append(room_id)
        
    return segment_ids_list

def change_button_interactive():
    return gr.update(interactive=vacuum.is_available)

def change_vacuum_status():

    """
    Function to toggle the vacuum status between available and not available.
    Prints the vacuum status before and after toggling.
    """
    print(f"Vacuum is now {'available' if vacuum.is_available else 'not available'}")  # Print current vacuum status
    vacuum.is_available = not vacuum.is_available  # Toggle the vacuum availability status
    print(f"Vacuum is now {'available' if vacuum.is_available else 'not available'}")  # Print updated vacuum status

async def start_button_on_click(level_choice, segment_ids):
    if not segment_ids:
        return gr.update(interactive=True)
    if level_choice not in ["L2", "L3", "B1"]:
        return gr.update(interactive=True)
    segment_ids_list = ast.literal_eval(segment_ids)
    level_choice = (int)((str)(level_choice).replace("L", "").replace("B", "-"))
    print(f"Selected Level: {level_choice}, Segment IDs: {segment_ids_list}")
    # vacuum.is_available = False  # Set vacuum to unavailable while cleaning
    await sweep_main(vacuum=vacuum, elevator=elevator, floor=level_choice, claen_segment_id_list=segment_ids_list)
    vacuum.is_available = True  # Set vacuum back to available after cleaning
    return gr.update(interactive=True)

async def custom_goto_level(initial_floor, target_floor):
    try:
        current_floor = int(str(initial_floor).replace('L', '').replace('B', '-'))
        target_floor = int(str(target_floor).replace('L', '').replace('B', '-'))
    except:
        print("Invalid floor input. Please enter a valid floor.")
        return
    
    if current_floor < FLOOR_MINIMUM or current_floor > FLOOR_MAXIMUM:
        print(f"Invalid current floor. Please enter a value between {FLOOR_MINIMUM} and {FLOOR_MAXIMUM}.")
        return
    
    if target_floor < FLOOR_MINIMUM or target_floor > FLOOR_MAXIMUM:
        print(f"Invalid target floor. Please enter a value between {FLOOR_MINIMUM} and {FLOOR_MAXIMUM}.")
        return
    
    await vacuum.login()
    await asyncio.sleep(2)
    
    if vacuum.map_floor == current_floor:
        await goto_level(vacuum=vacuum, elevator=elevator, current_level=current_floor, target_level=target_floor)
    else:
        vacuum.map_floor = current_floor
        await vacuum.api.load_multi_map(FLOOR_MAP_REFERENCE[str(current_floor)])
        await goto_level(vacuum=vacuum, elevator=elevator, current_level=current_floor, target_level=target_floor)

def get_qr_code():
    global ret_data_global
    img, ret_data = qr_login.generate_qr_code()
    ret_data_global = ret_data
    return img

def qr_code_login():
    def delayed_get_auth(ret_data):
        time.sleep(5)  # Wait for 5 seconds before getting auth
        auth = qr_login.get_auth(ret_data=ret_data)
        with open(f'{JSON_FILE_PATH}/{MIJIA_AUTH}', 'w') as f:
            json.dump(auth, f, indent=2)
        print("Login successful, auth saved to file.")
        
    img = get_qr_code()
    threading.Thread(target=delayed_get_auth, args=(ret_data_global,)).start()
    return img

segment_ids_list = None

with gr.Blocks(css="""
.centered-block {
    max-width: 60%;
    margin-left: auto;
    margin-right: auto;
    padding: 20px;
}
""") as demo:
    with gr.Column(elem_classes="centered-block"):
        gr.Markdown("## Vacuum Elevator Control Panel")
        
        # 每2秒更新一次的 Textbox
        vacuum_status_box = gr.Textbox(label="当前状态", interactive=False, value=vacuum.get_vacuum_status, every=2) 
        vacuum_floor_box = gr.Textbox(label="当前楼层", interactive=False, value=vacuum.get_map_floor, every=2)
        
        with gr.Tabs():
            with gr.TabItem("楼层清扫"):
                
                radio = gr.Radio(["L2", "L3", "B1"], label="请选择清扫的楼层")
                checkbox = gr.CheckboxGroup(choices=[], label="请选择清扫的区域", type="value", interactive=True)

                radio.change(
                    fn=update_checkboxes, 
                    inputs=radio, 
                    outputs=checkbox
                )
                
                segment_ids_output = gr.Textbox(label="选中的区域 ID 列表", interactive=False)
                
                
                checkbox.change(
                    fn=selected_rooms,
                    inputs=[radio, checkbox],
                    outputs=segment_ids_output
                )
                
                start_button = gr.Button("开始清扫")
                program_status = gr.Textbox(label="扫地机空闲", interactive=False, value=vacuum.get_availability, every=2)
                
                program_status.change(
                    fn=change_button_interactive,
                    inputs=None,
                    outputs=start_button
                )
                start_button.click(
                    fn=change_vacuum_status,
                    inputs=None,
                    outputs=program_status
                )
                start_button.click(
                    fn=start_button_on_click,
                    inputs=[radio, segment_ids_output],
                    outputs=start_button
                )
            with gr.TabItem("手动控制"):
                stop_button = gr.Button("停止")
                
                initial_map_floor_str = str(vacuum.map_floor).replace('-', 'B')
                if initial_map_floor_str.find('B') == -1:
                    initial_map_floor_str = 'L' + initial_map_floor_str
                
                initial_floor = gr.Radio(["L1", "L2", "L3", "B1"], label="当前楼层", value=initial_map_floor_str, interactive=True)
                target_floor = gr.Radio(["L1", "L2", "L3", "B1"], label="目标楼层", interactive=True)
                go_button = gr.Button("前往目标楼层")
                
                stop_command = RoborockCommand.APP_STOP
                stop_button.click(
                    fn=vacuum.stop,
                    inputs=None,
                    outputs=None
                )
                
                go_button.click(
                    fn=custom_goto_level,
                    inputs=[initial_floor, target_floor],
                    outputs=None
                )
            with gr.TabItem("登录"):
                login_button = gr.Button("登录")
                
                login_button.click(
                    fn=qr_code_login,
                    inputs=None,
                    outputs=gr.Image(type="pil", label="请扫码登录")
                )

            
demo.launch(server_name="0.0.0.0")
