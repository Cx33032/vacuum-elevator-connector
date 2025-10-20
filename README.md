# Elevator-Vacuum Connector

This project aims to build the connection between the family-use elevator and the Roborock vacuum cleaner (My model is G20S Ultra).

## Hardware Setup

Most of the family-use elevators are not supported with remote control. Therefore, to control the elevator, the easiest way is to connect the IoT switch with the elevator switch panel (I use Xiaomi giot.switch.v51ksm). 

## To-do List

- [x] Package all the Mijia Controlling program into a single class
- [x] Roborock Vacuum control (Go to the specific coordinates)
- [ ] Identification of elevator doors (open / close / elevator is not in this level) (**Cancelled**)
- [x] Correct functions in enter, exit the elevator
- [x] Set the program as a routine
- [ ] Record the running / error logs
- [x] Clean specific room
- [x] Washing and drying the mop
- [x] Improve the rooms setting (On the mobile application)
- [x] Clean the elevator
- [x] Sometimes can not change the map

## Reference
Home Assistant Roborock - [https://github.com/humbertogontijo/homeassistant-roborock](https://github.com/humbertogontijo/homeassistant-roborock)
Roborock Python API - [https://github.com/Python-roborock/python-roborock](https://github.com/Python-roborock/python-roborock)
