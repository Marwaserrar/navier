#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SimulationParameters:
    # Required parameter
    T: float

    # Optional parameters with default values
    DT: float = None
    dx: float = None
    dy: float = None
    Lx: float = 1.0
    Ly: float = 1.0
    KINEMATIC_VISCOSITY: float = 0.1
    DENSITY: float = 1.0

    # Optional integer parameters
    Nx: int = 51
    Ny: int = 51
    N_ITERATIONS: int = None
    N_PRESSURE_POISSON_ITERATIONS: Optional[int] = 50

    # Optional boolean parameters
    gif: Optional[bool] = False
    plot: Optional[bool] = True

    def __post_init__(self):
        # Force dx, dy from Nx, Ny if not consistent
        computed_dx = self.Lx / (self.Nx - 1)
        computed_dy = self.Ly / (self.Ny - 1)
        if self.dx is not None and abs(self.dx - computed_dx) > 1e-9:
            print(f"Forcing dx from {self.dx} to {computed_dx}")
            self.dx = computed_dx
        else:
            self.dx = computed_dx

        if self.dy is not None and abs(self.dy - computed_dy) > 1e-9:
            print(f"Forcing dy from {self.dy} to {computed_dy}")
            self.dy = computed_dy
        else:
            self.dy = computed_dy

        # If T, DT, N_ITERATIONS are partially set, unify them
        if self.T and self.DT and self.N_ITERATIONS:
            # check T == DT * N_ITERATIONS
            if abs(self.T - self.DT * self.N_ITERATIONS) > 1e-9:
                raise ValueError("T must equal DT*N_ITERATIONS")
        elif self.T and self.DT and (self.N_ITERATIONS is None):
            self.N_ITERATIONS = int(round(self.T / self.DT))
        elif self.T and self.N_ITERATIONS and (self.DT is None):
            self.DT = self.T / self.N_ITERATIONS
        else:
            # If not enough info, pick defaults
            if self.DT is None:
                self.DT = 0.01
            if self.N_ITERATIONS is None:
                self.N_ITERATIONS = int(round(self.T / self.DT))

        # final check for T == DT*N_ITERATIONS
        computed_T = self.DT * self.N_ITERATIONS
        if abs(self.T - computed_T) > 1e-9:
            raise ValueError("T must equal DT * N_ITERATIONS (or will be forced).")

    def __str__(self):
        s = "━━━━━━━━━━━━  Simulation Parameters ━━━━━━━━━━━━"
        s += f"\n\tT={self.T}\tDT={self.DT}\tN_ITERATIONS={self.N_ITERATIONS}"
        s += f"\n\tLx={self.Lx}\tNx={self.Nx}\tdx={self.dx}"
        s += f"\n\tLy={self.Ly}\tNy={self.Ny}\tdy={self.dy}"
        s += f"\n\tKINEMATIC_VISCOSITY={self.KINEMATIC_VISCOSITY}\tDENSITY={self.DENSITY}"
        s += f"\n\tN_PRESSURE_POISSON_ITERATIONS={self.N_PRESSURE_POISSON_ITERATIONS}"
        s += f"\n\tgif={self.gif}\tplot={self.plot}"
        s += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return s