import numpy as np
from datetime import datetime
from earth2studio.data import ARCO
from earth2studio.models.px.sfno import VARIABLES

def build_inputs(ts_iso: str) -> np.ndarray:
    ts = datetime.fromisoformat(ts_iso.replace("Z","+00:00"))
    ds = ARCO()
    da = ds(time=ts, variable=VARIABLES)
    arr = da.to_numpy()[None].astype("float32")
    return arr
