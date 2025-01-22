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

def generate_random_params():
    """
    Generate a random set of Navier-Stokes parameters with reduced (limited) ranges
    to minimize numerical instability.
    """

    while True:
        # 1. Random grid resolution (Narrow range: 30..50)
        Nx = random.randint(30, 50)
        Ny = random.randint(30, 50)

        # 2. Random domain size (Narrow range: 0.5..1.5)
        Lx = round(random.uniform(0.5, 1.5), 2)
        Ly = round(random.uniform(0.5, 1.5), 2)

        # 3. Derived dx, dy
        dx = Lx / (Nx - 1)
        dy = Ly / (Ny - 1)

        # 4. Random total time and iteration count (Reduced upper bounds)
        N_ITERATIONS = random.randint(50, 120)     # e.g., 50..120
        T = round(random.uniform(1.0, 2.0), 2)     # total time 1..2
        DT = T / N_ITERATIONS

        # 5. Random physical constants
        #    Keep narrower range for viscosity
        KINEMATIC_VISCOSITY = round(random.uniform(0.008, 0.015), 4)  # e.g., 0.008..0.015
        DENSITY = round(random.uniform(0.8, 1.2), 2)  # e.g., 0.8..1.2

        # 6. Basic stability check:
        #    DT < 0.5 * (dx^2) / KINEMATIC_VISCOSITY
        #    If stable, we break out of the loop
        if DT < 0.5 * (dx**2) / KINEMATIC_VISCOSITY:
            break

    # Additional parameters
    N_PRESSURE_POISSON_ITERATIONS = random.randint(30, 60)
    gif = bool(random.choice([False, True]))
    plot = True  # keep plotting on by default

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
    params = generate_random_params()

    # Print the random parameters for debugging
    print("Generated random simulation parameters:")
    print(params)

    # Send them to Kafka
    producer.send("simulation-parameters", value=params.__dict__)
    producer.flush()
    print("Random simulation parameters sent to the Kafka topic.")

if __name__ == "__main__":
    main()
