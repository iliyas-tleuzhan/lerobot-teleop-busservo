import csv
import os
import time
from typing import Dict, List, Optional


class TeleopLogger:
    def __init__(self, log_dir: str, joint_ids: List[int]):
        self.log_dir = log_dir
        self.joint_ids = joint_ids
        self.path: Optional[str] = None
        self._fh = None
        self._w = None

    def start(self):
        os.makedirs(self.log_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(self.log_dir, f"teleop_{ts}.csv")
        self._fh = open(self.path, "w", newline="", encoding="utf-8")
        self._w = csv.writer(self._fh)
        self._w.writerow(["unix_ms", "estop", "torque_on"] + [f"j{jid}" for jid in self.joint_ids] + ["marker"])
        self._fh.flush()

    def write(self, goals: Dict[int, int], estop: bool, torque_on: bool, marker: str = ""):
        if not self._w:
            return
        row = [int(time.time() * 1000), int(estop), int(torque_on)]
        for jid in self.joint_ids:
            row.append(int(goals[jid]))
        row.append(marker)
        self._w.writerow(row)
        self._fh.flush()

    def stop(self):
        if self._fh:
            try:
                self._fh.close()
            finally:
                self._fh = None
                self._w = None
