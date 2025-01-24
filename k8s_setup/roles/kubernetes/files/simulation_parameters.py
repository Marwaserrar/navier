#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Optional
import math

@dataclass
class SimulationParameters:
    T: float
    DT: float
    dx: float
    dy: float
    Lx: float
    Ly: float
    KINEMATIC_VISCOSITY: float
    DENSITY: float
    Nx: int
    Ny: int
    N_ITERATIONS: int
    N_PRESSURE_POISSON_ITERATIONS: Optional[int] = 50
    gif: Optional[bool] = True
    plot: Optional[bool] = True

    def __post_init__(self):
        if self.T != self.DT * self.N_ITERATIONS:
            raise ValueError("T must equal DT * N_ITERATIONS")
        if self.dx != self.Lx / (self.Nx - 1) or self.dy != self.Ly / (self.Ny - 1):
            raise ValueError("dx or dy mismatch.")
        if self.KINEMATIC_VISCOSITY <= 0 or self.DENSITY <= 0:
            raise ValueError("KINEMATIC_VISCOSITY and DENSITY must be positive.")
