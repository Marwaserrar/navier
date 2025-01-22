#!/usr/bin/env python3

import random
import math
import json

from kafka import KafkaProducer
from simulation_parameters import SimulationParameters

# Kafka configuration
producer = KafkaProducer(
    bootstrap_servers="kafka-internal:9092",  # Kafka service inside the cluster
    value_serializer=lambda v: json.dumps(v).encode("utf-8")  # Serialize message values as JSON
)

def generate_stable_params():
    """
    Generate a stable set of Navier-Stokes parameters with controlled randomization.
    Ensures that variables like Nx, Ny, dx, dy, and DT respect stability conditions.
    """
    # Fixed grid resolution (ensure stability)
    Nx = 40  # Fixed grid size in x-direction
    Ny = 40  # Fixed grid size in y-direction

    # Fixed domain size
    Lx = 1.0  # Fixed domain size in x-direction
    Ly = 1.0  # Fixed domain size in y-direction

    # Derived dx, dy
    dx = Lx / (Nx - 1)
    dy = Ly / (Ny - 1)

    # Random total time and iteration count (controlled range)
    N_ITERATIONS = random.randint(50, 100)  # Number of iterations
    T = round(random.uniform(1.0, 2.0), 2)  # Total simulation time
    DT = T / N_ITERATIONS  # Time step size

    # Random physical constants (controlled range)
    KINEMATIC_VISCOSITY = round(random.uniform(0.01, 0.02), 4)  # Kinematic viscosity
    DENSITY = round(random.uniform(0.9, 1.1), 2)  # Density

    # Ensure stability condition: DT < 0.5 * (dx^2) / KINEMATIC_VISCOSITY
    max_DT = 0.5 * (dx ** 2) / KINEMATIC_VISCOSITY
    if DT > max_DT:
        DT = max_DT  # Adjust DT to ensure stability

    # Additional parameters
    N_PRESSURE_POISSON_ITERATIONS = random.randint(30, 60)  # Pressure Poisson iterations
    gif = bool(random.choice([False, True]))  # Whether to generate a GIF
    plot = True  # Always plot the results

    return SimulationParameters(
        T=T,
        DT=DT,
        N_ITERATIONS=N_ITERATIONS,
        Nx=Nx,
        Lx=Lx,
        dx=dx,
        Ny=Ny,
        Ly=Ly,
        dy=dy,
        KINEMATIC_VISCOSITY=KINEMATIC_VISCOSITY,
        DENSITY=DENSITY,
        N_PRESSURE_POISSON_ITERATIONS=N_PRESSURE_POISSON_ITERATIONS,
        gif=gif,
        plot=plot
    )

def main():
    params = generate_stable_params()

    # Print the generated parameters for debugging
    print("Generated stable simulation parameters:")
    print(params)

    # Send them to Kafka
    producer.send("simulation-parameters", value=params.__dict__)
    producer.flush()
    print("Stable simulation parameters sent to the Kafka topic.")

if __name__ == "__main__":
    main()