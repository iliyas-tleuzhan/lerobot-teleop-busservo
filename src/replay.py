import csv
import time
from typing import Dict, List

from bus import DynamixelBus, BusConfig
from config_loader import load_config


def replay(csv_path: str, speed: float = 1.0):
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
    bus.set_position_mode_and_torque_on(joint_ids)

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            prev_ms = None
            for row in r:
                ms = int(row["unix_ms"])
                estop = bool(int(row["estop"]))
                torque_on = bool(int(row["torque_on"]))
                if estop or not torque_on:
                    prev_ms = ms
                    continue

                goals: Dict[int, int] = {}
                for jid in joint_ids:
                    goals[jid] = int(row[f"j{jid}"])

                if prev_ms is not None:
                    dt_ms = (ms - prev_ms) / max(speed, 1e-6)
                    time.sleep(max(0.0, dt_ms / 1000.0))

                bus.sync_write_goal_positions(goals)
                prev_ms = ms

        print("Replay complete.")
    finally:
        bus.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--speed", type=float, default=1.0)
    args = p.parse_args()

    replay(args.csv, speed=args.speed)
