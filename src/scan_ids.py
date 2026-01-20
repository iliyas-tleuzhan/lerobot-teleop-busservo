from bus import DynamixelBus, BusConfig
from config_loader import load_config


def main():
    cfg = load_config()
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

    found = []
    try:
        # Scan common ID range
        for dxl_id in range(1, 21):
            try:
                # read present position (will throw if no device)
                pos = bus.read_present_positions([dxl_id])[dxl_id]
                found.append((dxl_id, pos))
                print(f"Found ID {dxl_id}  present={pos}")
            except Exception:
                pass
    finally:
        bus.close()

    if not found:
        print("No devices found. Check baudrate/protocol/power/wiring.")
    else:
        print("IDs found:", [x[0] for x in found])


if __name__ == "__main__":
    main()
