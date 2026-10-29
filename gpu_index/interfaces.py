"""Deliberately separate useful-work and forward-contract boundaries."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Workload:
    task: str
    quality_target: str
    latency_limit_ms: float
    software_stack: str
    accepted_units_per_hour: float
    all_in_instance_hourly: float
    compatible: bool

    def cost_per_accepted_unit(self):
        if not self.compatible or not self.quality_target or not self.software_stack:
            raise ValueError('Qualified benchmark and compatible whole system required')
        if any(not math.isfinite(x) or x<=0 for x in (self.latency_limit_ms,self.accepted_units_per_hour,self.all_in_instance_hourly)):
            raise ValueError('Positive finite workload inputs required')
        return self.all_in_instance_hourly/self.accepted_units_per_hour

@dataclass(frozen=True)
class ForwardContract:
    delivery_start: str
    duration_months: int
    cluster_gpus: int
    prepayment: float
    guarantees: str
    cancellation_rights: str
    transferable: bool

    def value(self):
        raise NotImplementedError('No observed forward surface, capacity or contract rights model. Spot rental quotes do not value this contract.')
