#!/usr/bin/env python3

import random
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
    Generate a stable set of Navier-Stokes parameters with fixed values for most parameters
    and randomized KINEMATIC_VISCOSITY and DENSITY.
    """
    # Fixed values (from the docker run command)
    dx = 0.02040816326530612
    dy = 0.02040816326530612
    Nx = 50
    Ny = 50
    T = 10.0  # Total simulation time
    DT = 0.01  # Time step size
    N_PRESSURE_POISSON_ITERATIONS = 50  # Default value
    plot = True  # Always generate a plot
    gif = True  # Always generate a GIF

    # Calculate Lx and Ly based on dx, dy, Nx, and Ny
    Lx = dx * (Nx - 1)
    Ly = dy * (Ny - 1)

    # Randomize KINEMATIC_VISCOSITY and DENSITY
    KINEMATIC_VISCOSITY = round(random.uniform(0.001, 0.1), 4)  # Random kinematic viscosity
    DENSITY = round(random.uniform(0.5, 2.0), 2)  # Random density

    # Calculate N_ITERATIONS based on T and DT
    N_ITERATIONS = int(T / DT)

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