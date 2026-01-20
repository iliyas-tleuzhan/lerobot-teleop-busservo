import json
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

import yaml


@dataclass
class JointLimit:
    jid: int
    name: str
    range_min: int
    range_max: int
    homing_offset: int


@dataclass
class AppConfig:
    port: str
    baudrate: int
    protocol_version: float

    hz: int
    step_units: int
    use_present_position_as_start: bool
    home_strategy: str

    torque_enable_addr: int
    torque_enable_len: int
    goal_position_addr: int
    goal_position_len: int
    present_position_addr: int
    present_position_len: int
    operating_mode_addr: int
    operating_mode_len: int
    position_mode_value: int

    keymap: Dict[int, Tuple[str, str]]
    special_keys: Dict[str, str]

    joints: List[JointLimit]


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_joint_names(path: str) -> Dict[int, str]:
    data = load_yaml(path)
    return {int(k): str(v) for k, v in data.items()}


def load_limits_from_follower_json(path: str, joint_names: Dict[int, str]) -> List[JointLimit]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    joints = []
    for item in data.get("motors", []):
        jid = int(item["id"])
        name = joint_names.get(jid, f"joint_{jid}")
        joints.append(
            JointLimit(
                jid=jid,
                name=name,
                range_min=int(item["range_min"]),
                range_max=int(item["range_max"]),
                homing_offset=int(item.get("homing_offset", 0)),
            )
        )

    joints.sort(key=lambda j: j.jid)
    return joints


def load_config() -> AppConfig:
    cfg = load_yaml("config/robot.yaml")
    names = load_joint_names("config/joint_names.yaml")
    limits_path = cfg["limits"]["follower_limits_json"]
    joints = load_limits_from_follower_json(limits_path, names)

    keymap_raw = cfg["keymap"]
    keymap: Dict[int, Tuple[str, str]] = {}
    for jid, _name in names.items():
        k = f"j{jid}"
        if k in keymap_raw:
            dec_k, inc_k = keymap_raw[k]
            keymap[int(jid)] = (str(dec_k), str(inc_k))

    dyn = cfg["dynamixel"]
    ctrl = cfg["control"]
    robot = cfg["robot"]

    return AppConfig(
        port=str(robot["port"]),
        baudrate=int(robot["baudrate"]),
        protocol_version=float(robot["protocol_version"]),

        hz=int(ctrl["hz"]),
        step_units=int(ctrl["step_units"]),
        use_present_position_as_start=bool(ctrl["use_present_position_as_start"]),
        home_strategy=str(ctrl["home_strategy"]),

        torque_enable_addr=int(dyn["torque_enable_addr"]),
        torque_enable_len=int(dyn["torque_enable_len"]),
        goal_position_addr=int(dyn["goal_position_addr"]),
        goal_position_len=int(dyn["goal_position_len"]),
        present_position_addr=int(dyn["present_position_addr"]),
        present_position_len=int(dyn["present_position_len"]),
        operating_mode_addr=int(dyn["operating_mode_addr"]),
        operating_mode_len=int(dyn["operating_mode_len"]),
        position_mode_value=int(dyn["position_mode_value"]),

        keymap=keymap,
        special_keys=dict(cfg["special_keys"]),

        joints=joints,
    )
