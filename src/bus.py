from dataclasses import dataclass
from typing import Dict, List, Tuple

from dynamixel_sdk import (
    PortHandler,
    PacketHandler,
    GroupSyncWrite,
    GroupSyncRead,
    DXL_LOBYTE, DXL_HIBYTE, DXL_LOWORD, DXL_HIWORD,
)


@dataclass
class BusConfig:
    port: str
    baudrate: int
    protocol_version: float

    torque_enable_addr: int
    torque_enable_len: int
    goal_position_addr: int
    goal_position_len: int
    present_position_addr: int
    present_position_len: int
    operating_mode_addr: int
    operating_mode_len: int
    position_mode_value: int


class DynamixelBus:
    def __init__(self, cfg: BusConfig):
        self.cfg = cfg
        self.port = PortHandler(cfg.port)
        self.packet = PacketHandler(cfg.protocol_version)

        self.sync_write = GroupSyncWrite(self.port, self.packet, cfg.goal_position_addr, cfg.goal_position_len)
        self.sync_read = GroupSyncRead(self.port, self.packet, cfg.present_position_addr, cfg.present_position_len)

    def open(self):
        if not self.port.openPort():
            raise RuntimeError(f"Failed to open port {self.cfg.port}")
        if not self.port.setBaudRate(self.cfg.baudrate):
            raise RuntimeError(f"Failed to set baudrate {self.cfg.baudrate}")

    def close(self):
        try:
            self.port.closePort()
        except Exception:
            pass

    def _write1(self, dxl_id: int, addr: int, value: int):
        dxl_comm_result, dxl_error = self.packet.write1ByteTxRx(self.port, dxl_id, addr, value)
        if dxl_comm_result != 0:
            raise RuntimeError(f"Comm error write1 id={dxl_id}: {self.packet.getTxRxResult(dxl_comm_result)}")
        if dxl_error != 0:
            raise RuntimeError(f"DXL error write1 id={dxl_id}: {self.packet.getRxPacketError(dxl_error)}")

    def set_position_mode_and_torque_on(self, ids: List[int]):
        # Set operating mode then torque on
        for dxl_id in ids:
            self._write1(dxl_id, self.cfg.operating_mode_addr, self.cfg.position_mode_value)
        for dxl_id in ids:
            self._write1(dxl_id, self.cfg.torque_enable_addr, 1)

    def torque(self, ids: List[int], on: bool):
        for dxl_id in ids:
            self._write1(dxl_id, self.cfg.torque_enable_addr, 1 if on else 0)

    def add_sync_read_ids(self, ids: List[int]):
        self.sync_read.clearParam()
        for dxl_id in ids:
            ok = self.sync_read.addParam(dxl_id)
            if not ok:
                raise RuntimeError(f"Failed to add sync read param for id {dxl_id}")

    def read_present_positions(self, ids: List[int]) -> Dict[int, int]:
        self.add_sync_read_ids(ids)
        dxl_comm_result = self.sync_read.txRxPacket()
        if dxl_comm_result != 0:
            raise RuntimeError(f"Comm error syncRead: {self.packet.getTxRxResult(dxl_comm_result)}")

        out: Dict[int, int] = {}
        for dxl_id in ids:
            if not self.sync_read.isAvailable(dxl_id, self.cfg.present_position_addr, self.cfg.present_position_len):
                raise RuntimeError(f"Present position not available for id {dxl_id}")

            # 4-byte little-endian
            b0 = self.sync_read.getData(dxl_id, self.cfg.present_position_addr, 1)
            b1 = self.sync_read.getData(dxl_id, self.cfg.present_position_addr + 1, 1)
            b2 = self.sync_read.getData(dxl_id, self.cfg.present_position_addr + 2, 1)
            b3 = self.sync_read.getData(dxl_id, self.cfg.present_position_addr + 3, 1)
            val = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
            out[dxl_id] = int(val)
        return out

    def sync_write_goal_positions(self, goals: Dict[int, int]):
        self.sync_write.clearParam()
        for dxl_id, pos in goals.items():
            # pack 4 bytes
            param = [
                DXL_LOBYTE(DXL_LOWORD(pos)),
                DXL_HIBYTE(DXL_LOWORD(pos)),
                DXL_LOBYTE(DXL_HIWORD(pos)),
                DXL_HIBYTE(DXL_HIWORD(pos)),
            ]
            ok = self.sync_write.addParam(dxl_id, bytes(param))
            if not ok:
                raise RuntimeError(f"Failed to add sync write param for id {dxl_id}")

        dxl_comm_result = self.sync_write.txPacket()
        if dxl_comm_result != 0:
            raise RuntimeError(f"Comm error syncWrite: {self.packet.getTxRxResult(dxl_comm_result)}")
