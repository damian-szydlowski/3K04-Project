#Data structure format (each sample is a dict):
#  "t_s": float,     # seconds (wall-clock)
#  "raw": int,       # raw device units (lossless)
#  "marker": str     # one of: "--", "VS", "VP", "()"

import time
import json
import os
from typing import List, Dict, Optional

ALLOWED_MARKERS = {"--", "VS", "VP", "()"} #these are the 4 types of inputs that can be recieved from the pacemaker

# current time
def now_s() -> float:
    return time.time()

class EgramModel:
    """
    Model to hold egram for the GUI
    - append_sample(...) to add one sample
    - get_samples() to read all captured samples (for plotting/inspection)
    - reset(session_id=...) to start a new capture
    - save_jsonl(path) / load_jsonl(path) for simple persistence (future use)
    """

    def __init__(self, session_id: str = "sess-001"):
        self.meta: Dict = {
            "session_id": session_id,
            "started_at_unix": now_s(),
            "patient_id": None,
            "sampling_period_s": None,
            "device_params_snapshot": None,
        }
        self._samples: List[Dict] = []

    def append_sample(self, raw: int, marker: str = "--", t_s: Optional[float] = None) -> None:
        """
        Single egram sample.
        - raw: integer (keep exactly as received later)
        - marker: "--", "VS", "VP", or "()"
        - t_s: optional timestamp in seconds (defaults to now())
        """
        if marker not in ALLOWED_MARKERS:
            marker = "--"
        sample = {
            "t_s": float(t_s if t_s is not None else now_s()),
            "raw": int(raw),
            "marker": marker,
        }
        self._samples.append(sample)

    def get_samples(self) -> List[Dict]:
        return list(self._samples) #return the samples we have

    # start a new capture 
    def reset(self, session_id: str = "sess-001") -> None:

        self._samples.clear()
        self.meta["session_id"] = session_id
        self.meta["started_at_unix"] = now_s()

    def to_json_lines(self) -> str:
        """
        First line: {"meta": {...}}
        Then one line per sample: {"sample": {...}}
        """
        lines = [json.dumps({"meta": self.meta})]
        for s in self._samples:
            lines.append(json.dumps({"sample": s}))
        return "\n".join(lines)

    def save_jsonl(self, path: str) -> None:
        """Write JSON Lines to disk (creates folders if needed)."""
        d = os.path.dirname(os.path.abspath(path))
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json_lines())

    def load_jsonl(self, path: str) -> None:
        """Load a previously saved capture into this model."""
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        meta = None
        samples: List[Dict] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                if "meta" in obj:
                    meta = obj["meta"]
                elif "sample" in obj:
                    samples.append(obj["sample"])
        if meta is None:
            raise ValueError("Invalid JSONL: missing meta header")
        self.meta = meta
        self._samples = samples
