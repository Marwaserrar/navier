#!/usr/bin/env python3

import json
import random
import math
from kafka import KafkaProducer
from simulation_parameters import SimulationParameters

# Kafka producer configuration
producer = KafkaProducer(
    bootstrap_servers="kafka-internal:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Fixed parameters
FIXED_ITERATIONS = 500 

def main():
    """
    Randomizes simulation parameters while ensuring T = DT * N_ITERATIONS exactly.
    """

    # 1. Define fixed domain sizes (can also be randomized if needed)
    Lx = 1.0  # meters
    Ly = 1.0  # meters

    # 2. Randomize grid resolution Nx and Ny within [30, 60]
    Nx = random.randint(30, 60)
    Ny = random.randint(30, 60)

    # 3. Randomize Kinematic Viscosity in [0.01, 0.1] m²/s
    KINEMATIC_VISCOSITY = round(random.uniform(0.01, 0.1), 4)

    # 4. Randomize Density in [0.5, 2.0] kg/m³
    DENSITY = round(random.uniform(0.5, 2.0), 4)

    # 5. Compute spatial steps dx and dy
    dx = Lx / (Nx - 1)
    dy = Ly / (Ny - 1)

    # 6. Compute maximum stable DT based on diffusion
    dt_max_diffusion = 0.5 * (dx ** 2) / KINEMATIC_VISCOSITY

    # 7. Define a CFL-like condition for advection (assuming a characteristic velocity U)
    U = 1.0  # m/s
    CFL = 0.5  # CFL number
    dt_max_advection = CFL * dx / U

    # 8. Compute the overall maximum DT
    dt_max = min(dt_max_diffusion, dt_max_advection)

    # 9. Randomize DT within [0.2 * dt_max, 0.8 * dt_max]
    DT = round(random.uniform(0.2 * dt_max, 0.8 * dt_max), 6)

    # 10. Compute T based on fixed iterations
    T = round(DT * FIXED_ITERATIONS, 6)

    # 11. Create SimulationParameters instance
    params = SimulationParameters(
        T=T,
        Lx=Lx,
        Ly=Ly,
        Nx=Nx,
        Ny=Ny,
        KINEMATIC_VISCOSITY=KINEMATIC_VISCOSITY,
        DENSITY=DENSITY,
        DT=DT,
        N_ITERATIONS=FIXED_ITERATIONS, 
        gif=False,
        plot=True
    )

    # 12. Print parameters for debugging
    print("Generated randomized simulation parameters (with fixed iterations):")
    print(json.dumps(params.__dict__, indent=4))

    # 13. Send parameters to Kafka topic 'simulation-parameters'
    producer.send("simulation-parameters", value=params.__dict__)
    producer.flush()
    print("Parameters sent to Kafka topic: 'simulation-parameters'.")

if __name__ == "__main__":
    main()