import time
from typing import Dict, List

import keyboard

from bus import DynamixelBus, BusConfig
from config_loader import load_config
from logger import TeleopLogger


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def build_home_goals(joints, strategy: str) -> Dict[int, int]:
    goals = {}
    for j in joints:
        if strategy == "from_json_offset":
            # your JSON has homing_offset; not always an absolute position.
            # we keep this as an optional strategy but default to midpoint.
            # If your setup expects offset-based homing, you can adjust here later.
            mid = (j.range_min + j.range_max) // 2
            goals[j.jid] = clamp(mid + j.homing_offset, j.range_min, j.range_max)
        else:
            goals[j.jid] = (j.range_min + j.range_max) // 2
    return goals


def main():
    cfg = load_config()
    joint_ids: List[int] = [j.jid for j in cfg.joints]

    bus = DynamixelBus(
        BusConfig(
            port=cfg.port,
            baudrate=cfg.baudrate,
            protocol_version=cfg.protocol_version,
            torque_enable_addr=cfg.torque_enable_addr,
            torque_enable_len=cfg.torque_enable_len,
            goal_position_addr=cfg.goal_position_addr,
            goal_position_len=cfg.goal_position_len,
            present_position_addr=cfg.present_position_addr,
            present_position_len=cfg.present_position_len,
            operating_mode_addr=cfg.operating_mode_addr,
            operating_mode_len=cfg.operating_mode_len,
            position_mode_value=cfg.position_mode_value,
        )
    )

    bus.open()

    # Ensure correct mode and torque
    bus.set_position_mode_and_torque_on(joint_ids)
    torque_on = True

    # Choose initial goals
    if cfg.use_present_position_as_start:
        try:
            present = bus.read_present_positions(joint_ids)
            goals = {jid: int(present[jid]) for jid in joint_ids}
        except Exception:
            goals = build_home_goals(cfg.joints, cfg.home_strategy)
    else:
        goals = build_home_goals(cfg.joints, cfg.home_strategy)

    # Apply safety clamp to initial goals
    for j in cfg.joints:
        goals[j.jid] = clamp(goals[j.jid], j.range_min, j.range_max)

    logger = TeleopLogger("logs", joint_ids)
    logger.start()

    print("\n=== LeRobot Bus-Servo Teleop ===")
    print(f"COM: {cfg.port}  baud: {cfg.baudrate}  protocol: {cfg.protocol_version}")
    print("Joint limits loaded from config/Group_Follower.json")
    print("\nKeys:")
    for j in cfg.joints:
        dec_k, inc_k = cfg.keymap.get(j.jid, ("?", "?"))
        print(f"  ID {j.jid:>2} {j.name:<14}  {dec_k}/{inc_k}  range[{j.range_min},{j.range_max}]")
    print(f"\n  HOME: {cfg.special_keys['home']}")
    print(f"  Torque toggle: {cfg.special_keys['torque_toggle']}")
    print(f"  E-STOP (hold): {cfg.special_keys['estop_hold']}")
    print(f"  Marker: {cfg.special_keys['marker']}")
    print(f"  Quit: {cfg.special_keys['quit']}\n")

    dt = 1.0 / float(cfg.hz)
    estop = False

    try:
        while True:
            t0 = time.time()
            marker = ""

            if keyboard.is_pressed(cfg.special_keys["quit"]):
                print("Quit.")
                break

            estop = keyboard.is_pressed(cfg.special_keys["estop_hold"])

            if keyboard.is_pressed(cfg.special_keys["marker"]):
                marker = "MARK"

            if keyboard.is_pressed(cfg.special_keys["home"]):
                goals = build_home_goals(cfg.joints, cfg.home_strategy)
                for j in cfg.joints:
                    goals[j.jid] = clamp(goals[j.jid], j.range_min, j.range_max)

            if keyboard.is_pressed(cfg.special_keys["torque_toggle"]):
                # simple debounce
                time.sleep(0.15)
                torque_on = not torque_on
                bus.torque(joint_ids, torque_on)
                print(f"Torque {'ON' if torque_on else 'OFF'}")

            if not estop and torque_on:
                for j in cfg.joints:
                    if j.jid not in cfg.keymap:
                        continue
                    dec_k, inc_k = cfg.keymap[j.jid]
                    if keyboard.is_pressed(dec_k):
                        goals[j.jid] -= cfg.step_units
                    if keyboard.is_pressed(inc_k):
                        goals[j.jid] += cfg.step_units

                    goals[j.jid] = clamp(goals[j.jid], j.range_min, j.range_max)

                bus.sync_write_goal_positions(goals)

            logger.write(goals, estop=estop, torque_on=torque_on, marker=marker)

            elapsed = time.time() - t0
            if elapsed < dt:
                time.sleep(dt - elapsed)

    finally:
        logger.stop()
        bus.close()
        print("Closed bus + logger.")
        if logger.path:
            print("Log saved:", logger.path)


if __name__ == "__main__":
    main()
