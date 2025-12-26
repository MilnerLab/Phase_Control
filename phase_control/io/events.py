from dataclasses import dataclass


TOPIC_SPECTRUM_ARRIVED = "io.spectrum_arrived"
TOPIC_ACQ_ERROR = "io.acquisition_error"


@dataclass(frozen=True)
class SpectrumArrived:
    timestamp: float
    device_index: int
