import platform
import os
import subprocess
from subprocess import Popen
import psutil
import signal

import time

import gradio as gr

system = platform.system()
script_pid = None
def kill_proc_tree(pid, including_parent=True):
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        # Process already terminated
        return

    children = parent.children(recursive=True)
    for child in children:
        try:
            os.kill(child.pid, signal.SIGTERM)  # or signal.SIGKILL
        except OSError:
            pass
    if including_parent:
        try:
            os.kill(parent.pid, signal.SIGTERM)  # or signal.SIGKILL
        except OSError:
            pass

def kill_process(pid, process_name=""):
    # Check if the system is Windows
    if(system=="Windows"):
        cmd = "taskkill /t /f /pid %s" % pid
        # os.system(cmd)
        subprocess.run(cmd,shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        kill_proc_tree(pid)
    print(process_name + " is terminated.")
    
def change_script_status(status):
    global script_pid
    status = status.lower()
    if status == 'run':
        cmd = "python frontend.py"
        script_pid = Popen(cmd, shell=True)
    else:
        kill_process(script_pid.pid, "frontend.py")
        script_pid = None

def restart_script():
    try:
        change_script_status("stop")
        time.sleep(3)  # Wait for the script to stop
        change_script_status("run")
    except:
        pass

def get_script_status():
    if script_pid is None or not psutil.pid_exists(script_pid.pid):
        return "Script is not running."
    else:
        return f"Script is running with PID: {script_pid.pid}"    
        
with gr.Blocks() as run_interface:
    gr.Markdown("## Run Interface")
    
    gr.Textbox(label="Script Status", value=get_script_status, interactive=False, every=2)
    
    with gr.Row():
        run_button = gr.Button("Run")
        stop_button = gr.Button("Stop")
        restart_button = gr.Button("Restart")
        
    run_button.click(fn=change_script_status, inputs=run_button, outputs=None)
    stop_button.click(fn=change_script_status, inputs=stop_button, outputs=None)
    restart_button.click(fn=restart_script, inputs=None, outputs=None)
    
run_interface.launch(server_name="0.0.0.0", server_port=7861)