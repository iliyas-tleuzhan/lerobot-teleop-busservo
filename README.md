# LeRobot SO101 Teleoperation (Bus Servo / Dynamixel-style)
<p align="center">
  <img src="assets/gif.gif" width="300">
</p>

## Teleoperation + safety + logging + replay for a 6-DOF LeRobot SO101 setup using daisy-chained smart servos on a single TTL bus.
<p align="center">
  <img src="assets/both_lerobots.jpeg" width="250" height="325">
  <img src="assets/follower.jpeg" width="250" height="325">
  <img src="assets/assembling_follower.jpeg" width="250" height="325">
</p>

## Hardware topology
<p align="center">
  <img src="assets/connection.jpg" width="250" height="325">
</p>
Laptop → USB → USB↔TTL adapter board → Servo bus → (Motor 1 → Motor 2 → … → Motor 6)

## Leader and Follower Arms
<p align="center">
  <img src="assets/follower_close_up.jpeg" width="250" height="325">
  <img src="assets/leader.jpeg" width="250" height="325">
</p>
  
## Features
- ✅ Keyboard teleoperation
- ✅ Safety clamps using real joint ranges (`range_min/range_max`) from `Group_Follower.json`
- ✅ CSV logging
- ✅ Replay from logs
- ✅ Scan tool to verify IDs

## Setup (Windows)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
