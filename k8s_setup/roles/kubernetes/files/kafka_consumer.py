#!/usr/bin/env python3

import os
import base64
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from kafka import KafkaConsumer
from google.cloud import storage
from google.oauth2 import service_account
from datetime import datetime

from simulation_parameters import SimulationParameters

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more granular logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

##############################################################################
# 1. Load GCP credentials from the mounted JSON file
##############################################################################
GCP_CREDENTIALS = None
GCP_CRED_PATH = "/secrets/gcp_cred.json"  # Path to the mounted JSON key file

try:
    logging.debug(f"Attempting to load GCP credentials from {GCP_CRED_PATH}.")
    with open(GCP_CRED_PATH, "r") as f:
        creds_json = json.load(f)
        GCP_CREDENTIALS = service_account.Credentials.from_service_account_info(creds_json)
        logging.info("Loaded GCP credentials from mounted JSON file.")
except Exception as e:
    logging.error(f"Failed to load GCP credentials from {GCP_CRED_PATH}: {e}")

##############################################################################
# 2. Kafka and GCP Settings
##############################################################################
_consumer = KafkaConsumer(
    "simulation-parameters",
    bootstrap_servers="kafka-internal:9092",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

BUCKET_NAME = "state-sdtd-1"

# Ensure the results directory exists
RESULTS_DIR = "/tmp/simulation_results"
os.makedirs(RESULTS_DIR, exist_ok=True)
logging.debug(f"Ensured that results directory '{RESULTS_DIR}' exists.")

##############################################################################
# 3. GCP Upload Function (Uses in-memory credentials)
##############################################################################
def upload_to_gcp(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to a GCP bucket using in-memory credentials."""
    logging.info(f"Attempting to upload '{source_file_name}' to bucket '{bucket_name}' as '{destination_blob_name}'.")

    if not GCP_CREDENTIALS:
        logging.error("No GCP credentials available; skipping upload.")
        return

    try:
        client = storage.Client(credentials=GCP_CREDENTIALS)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logging.info(f"Successfully uploaded '{source_file_name}' to '{destination_blob_name}' in bucket '{bucket_name}'.")

        # Verify upload by listing the blob
        if blob.exists():
            logging.info(f"Verified that '{destination_blob_name}' exists in bucket '{bucket_name}'.")
        else:
            logging.error(f"Uploaded blob '{destination_blob_name}' does not exist in bucket '{bucket_name}'.")
    except Exception as e:
        logging.error(f"Failed to upload '{source_file_name}' to GCP: {e}")
##############################################################################
# 4. Numerical Methods
##############################################################################
def central_diff_x(f, dx):
    cdx = np.zeros_like(f)
    cdx[1:-1, 1:-1] = (f[1:-1, 2:] - f[1:-1, 0:-2]) / (2 * dx)
    return cdx

def central_diff_y(f, dy):
    cdy = np.zeros_like(f)
    cdy[1:-1, 1:-1] = (f[2:, 1:-1] - f[0:-2, 1:-1]) / (2 * dy)
    return cdy

def laplace(f, dx, dy):
    """5-point stencil for Laplacian."""
    lap = np.zeros_like(f)
    lap[1:-1, 1:-1] = (
        f[1:-1, 0:-2]
        + f[1:-1, 2:]
        + f[0:-2, 1:-1]
        + f[2:, 1:-1]
        - 4 * f[1:-1, 1:-1]
    ) / (dx * dy)
    return lap

def open_top_lid_BC_velocity(u, v):
    """Boundary condition that sets the top lid (u at y=-1) to velocity 1.0."""
    u[-1, :] = 1.0
    return u, v

def homogeneous_boundary_condition_velocity(u, v):
    """Zero velocity on the other boundaries."""
    u[0, :], u[-1, :], u[:, 0], u[:, -1] = 0.0, 0.0, 0.0, 0.0
    v[0, :], v[-1, :], v[:, 0], v[:, -1] = 0.0, 0.0, 0.0, 0.0
    return u, v

BOUNDARY_CONDITION = open_top_lid_BC_velocity

##############################################################################
# 5. Navier-Stokes Solver
##############################################################################
def run_navier_stokes_solver(sim_params: SimulationParameters):
    logging.info(f"Starting simulation with parameters: {sim_params}")

    # Grid/time setup
    dx, dy = sim_params.dx, sim_params.dy
    T, DT = sim_params.T, sim_params.DT
    Lx, Ly = sim_params.Lx, sim_params.Ly
    Nx, Ny = sim_params.Nx, sim_params.Ny
    N_ITERATIONS = sim_params.N_ITERATIONS
    KINEMATIC_VISCOSITY = sim_params.KINEMATIC_VISCOSITY
    DENSITY = sim_params.DENSITY
    do_plot = sim_params.plot
    do_gif = sim_params.gif
    n_poisson_iters = sim_params.N_PRESSURE_POISSON_ITERATIONS

    xs = np.linspace(0.0, Lx, Nx)
    ys = np.linspace(0.0, Ly, Ny)
    X, Y = np.meshgrid(xs, ys)

    # Initialize velocity & pressure fields
    u_prev = np.zeros_like(X)
    v_prev = np.zeros_like(X)
    p_prev = np.zeros_like(X)

    # Save initial state for final plotting
    u_initial = u_prev.copy()
    v_initial = v_prev.copy()
    p_initial = p_prev.copy()

    # Lists for GIF
    u_list, v_list, p_list = [], [], []

    # Main simulation loop
    for step in range(1, N_ITERATIONS + 1):
        if DT > 0.5 * (dx ** 2) / KINEMATIC_VISCOSITY:
            raise ValueError("Time step too large for stability.")

        d_u_prev__d_x = central_diff_x(u_prev, dx)
        d_u_prev__d_y = central_diff_y(u_prev, dy)
        d_v_prev__d_x = central_diff_x(v_prev, dx)
        d_v_prev__d_y = central_diff_y(v_prev, dy)
        laplace_u_prev = laplace(u_prev, dx, dy)
        laplace_v_prev = laplace(v_prev, dx, dy)

        # (1) Velocity prediction
        u_star = u_prev + DT * (
            -(u_prev * d_u_prev__d_x + v_prev * d_u_prev__d_y)
            + KINEMATIC_VISCOSITY * laplace_u_prev
        )
        v_star = v_prev + DT * (
            -(u_prev * d_v_prev__d_x + v_prev * d_v_prev__d_y)
            + KINEMATIC_VISCOSITY * laplace_v_prev
        )

        u_star, v_star = homogeneous_boundary_condition_velocity(u_star, v_star)
        u_star, v_star = BOUNDARY_CONDITION(u_star, v_star)

        # (2) Pressure Poisson
        rhs = (central_diff_x(u_star, dx) + central_diff_y(v_star, dy)) / DT
        for _ in range(n_poisson_iters):
            p_prev[1:-1, 1:-1] = 0.25 * (
                p_prev[1:-1, 0:-2]
                + p_prev[1:-1, 2:]
                + p_prev[0:-2, 1:-1]
                + p_prev[2:, 1:-1]
                - dx * dy * rhs[1:-1, 1:-1]
            )
            # Neumann boundaries for p
            p_prev[:, -1] = p_prev[:, -2]
            p_prev[:, 0] = p_prev[:, 1]
            p_prev[-1, :] = p_prev[-2, :]
            p_prev[0, :] = p_prev[1, :]

        # (3) Velocity correction
        dp_dx = central_diff_x(p_prev, dx)
        dp_dy = central_diff_y(p_prev, dy)
        u_next = u_star - DT / DENSITY * dp_dx
        v_next = v_star - DT / DENSITY * dp_dy

        u_prev, v_prev = u_next, v_next

        # Save for GIF
        u_list.append(u_next.copy())
        v_list.append(v_next.copy())
        p_list.append(p_prev.copy())

    # Plot final result
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"{RESULTS_DIR}/simulation_plot_{timestamp}.png"

    if do_plot:
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=100)

        # Initial
        ax1.set_title("Champ de vitesse et pression initiaux")
        im1 = ax1.imshow(
            p_initial, extent=[0, Lx, 0, Ly], origin="lower", cmap="viridis", alpha=0.8
        )
        ax1.streamplot(X, Y, u_initial, v_initial, color="black")
        fig.colorbar(im1, ax=ax1, label="Pression")
        ax1.set_xlabel("x")
        ax1.set_ylabel("y")

        # Final
        p_final = p_prev.copy()
        u_final = u_prev.copy()
        v_final = v_prev.copy()

        ax2.set_title("Champ de vitesse et pression finaux")
        im2 = ax2.imshow(
            p_final, extent=[0, Lx, 0, Ly], origin="lower", cmap="viridis", alpha=0.8
        )
        ax2.streamplot(X, Y, u_final, v_final, color="black")
        fig.colorbar(im2, ax=ax2, label="Pression")
        ax2.set_xlabel("x")
        ax2.set_ylabel("y")

        plt.tight_layout()
        plt.savefig(plot_filename)
        logging.info(f"Generated initial/final states plot in '{plot_filename}'")
        plt.close(fig)

    if do_gif:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        pressure_im = ax.imshow(
            p_list[0], extent=[0, Lx, 0, Ly], origin="lower", cmap="viridis", alpha=0.8
        )
        plt.colorbar(pressure_im, ax=ax, label="Pression")

        quiver = ax.quiver(
            X[::2], Y[::2], u_list[0][::2], v_list[0][::2], scale=1, scale_units="xy", color="black"
        )

        def animate(i):
            quiver.set_UVC(u_list[i][::2], v_list[i][::2])
            pressure_im.set_array(p_list[i])
            ax.set_title(f"Champ de vitesse et pression - Iter {i+1}")
            return quiver, pressure_im

        anim = FuncAnimation(fig, animate, frames=len(u_list), blit=True, interval=100)
        gif_filename = f"{RESULTS_DIR}/simulation_animation_{timestamp}.gif"
        anim.save(gif_filename, writer="pillow")
        logging.info(f"Generated GIF animation in '{gif_filename}'")
        plt.close(fig)

    # Upload final PNG to GCP (in-memory credentials)
    upload_to_gcp(
        bucket_name=BUCKET_NAME,
        source_file_name=plot_filename,
        destination_blob_name=f"simulation_results/simulation_plot_{timestamp}.png",
    )

    logging.info("End of simulation.")


def main():
    logging.info("Kafka consumer started. Waiting for simulation parameters...")
    from simulation_parameters import SimulationParameters

    for message in _consumer:
        try:
            params = SimulationParameters(**message.value)
            logging.info(f"Received simulation parameters: {params}")
            run_navier_stokes_solver(params)
        except Exception as e:
            logging.error(f"Error during simulation: {e}")

if __name__ == "__main__":
    main()
