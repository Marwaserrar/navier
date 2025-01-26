#!/usr/bin/env python3

import random
import json
from kafka import KafkaProducer
from simulation_parameters import SimulationParameters

# Kafka configuration
producer = KafkaProducer(
    bootstrap_servers="kafka-internal:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def generate_stable_params():
    """
    Generate a stable set of Navier-Stokes parameters with dynamic values that respect simulation stability conditions.
    One parameter (e.g., grid size) dynamically influences the ranges of others (e.g., time step, viscosity).
    """
    # Fixed domain size (Lx and Ly set to 1.0 for simplicity)
    Lx = 1.0
    Ly = 1.0

    # Randomize grid resolution (Nx and Ny between 30 and 80)
    Nx = random.randint(30, 80)
    Ny = random.randint(30, 80)
    dx = Lx / (Nx - 1)
    dy = Ly / (Ny - 1)

    # Randomize kinematic viscosity within a reasonable range
    KINEMATIC_VISCOSITY = random.uniform(0.001, 0.1)

    # Compute maximum allowable time step based on stability condition
    max_dt = 0.5 * (dx ** 2) / KINEMATIC_VISCOSITY

    # Choose DT safely within 20% to 80% of max_dt to avoid instability
    DT = random.uniform(0.2 * max_dt, 0.8 * max_dt)

    # Determine number of iterations to ensure sufficient simulation time
    N_ITERATIONS = random.randint(100, 1000)

    # Compute total simulation time T
    T = DT * N_ITERATIONS

    # Randomize density within a reasonable range
    DENSITY = random.uniform(0.5, 2.0)

    # Fixed number of Poisson iterations for pressure correction
    N_PRESSURE_POISSON_ITERATIONS = 50

    return SimulationParameters(
        T=T,
        DT=DT,
        dx=dx,
        dy=dy,
        Lx=Lx,
        Ly=Ly,
        KINEMATIC_VISCOSITY=KINEMATIC_VISCOSITY,
        DENSITY=DENSITY,
        Nx=Nx,
        Ny=Ny,
        N_ITERATIONS=N_ITERATIONS,
        N_PRESSURE_POISSON_ITERATIONS=N_PRESSURE_POISSON_ITERATIONS,
        gif=False,
        plot=True
    )

def main():
    # Generate stable parameters
    params = generate_stable_params()

    # Print the generated parameters for debugging
    print("Generated simulation parameters:")
    print(params)

    # Send them to Kafka
    producer.send("simulation-parameters", value=params.__dict__)
    producer.flush()
    print("Simulation parameters sent to the Kafka topic.")

if __name__ == "__main__":
    main()