# Elevator-Vacuum Connector

This project aims to build the connection between the family-use elevator and the Roborock vacuum cleaner (My model is G20S Ultra).

## Hardware Setup

Most of the family-use elevators are not supported with remote control. Therefore, to control the elevator, the easiest way is to connect the IoT switch with the elevator switch panel (I use Xiaomi giot.switch.v51ksm). 

## Get Started

```shell
python -m pip install -r requirements.txt
```

### Connection Settings

#### Obtain Home Assistant API Key

The Home Assistant is used to check the status of the vacuum. To obtain the API key, the method is the same as [Hass Agent](https://www.hass-agent.io/2.1/getting-started/initial-setup/). Once get the API key, change the API key section in ```const.py```

#### Home Assistant Set-up

The community version of [homeassistant-roborock](https://github.com/humbertogontijo/homeassistant-roborock) is needed. The installation is recommended via HACS. Please check the [homeassistant-roborock](https://github.com/humbertogontijo/homeassistant-roborock) for further details.

#### Mijia and Roborock Credentials

In ```jsons/credentials.json```, change the username to your mijia username. The email and password is for your roborock account. (Probobly will implement environment variable in the future)

### Rooms and Critical Coordinates

#### Rooms in Each Level

#### Important Coordinates

## Reference
Home Assistant Roborock - [https://github.com/humbertogontijo/homeassistant-roborock](https://github.com/humbertogontijo/homeassistant-roborock)
Roborock Python API - [https://github.com/Python-roborock/python-roborock](https://github.com/Python-roborock/python-roborock)
