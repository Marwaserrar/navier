#!/usr/bin/env python3
import sys
import os
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

# --------------------- CONFIGURE LOGGING ---------------------
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)



# --------------------- ARGUMENT HANDLING ---------------------
if len(sys.argv) != 2:
    logging.error("Usage: python kafka_consumer.py <pod_id>")
    sys.exit(1)

try:
    POD_ID = int(sys.argv[1])
    logging.info(f"Running consumer with POD ID: {POD_ID}")
except ValueError:
    logging.error("Invalid POD ID. It must be an integer.")
    sys.exit(1)



# --------------------- GCP CREDENTIAL LOADING ---------------------
GCP_CREDENTIALS = None
GCP_CRED_PATH = "/secrets/gcp_cred.json"

try:
    logging.debug(f"Attempting to load GCP credentials from {GCP_CRED_PATH}.")
    with open(GCP_CRED_PATH, "r") as f:
        creds_json = json.load(f)
        GCP_CREDENTIALS = service_account.Credentials.from_service_account_info(creds_json)
        logging.info("Successfully loaded GCP credentials from mounted JSON file.")
except FileNotFoundError:
    logging.error(f"GCP credentials file not found at {GCP_CRED_PATH}.")
except json.JSONDecodeError:
    logging.error(f"Invalid JSON format in GCP credentials file at {GCP_CRED_PATH}.")
except Exception as e:
    logging.error(f"Failed to load GCP credentials: {e}")

# ----------------------- KAFKA SETTINGS -----------------------
_consumer = KafkaConsumer(
    "simulation-parameters",
    bootstrap_servers="kafka-internal:9092",
    group_id='shared-consumer-group',
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

BUCKET_NAME = "bucket-marwa"
RESULTS_DIR = "/tmp/simulation_results"
os.makedirs(RESULTS_DIR, exist_ok=True)
logging.debug(f"Ensured that results directory '{RESULTS_DIR}' exists.")

# ------------------- GCP UPLOAD FUNCTION -------------------
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
        if blob.exists():
            logging.info(f"Verified that '{destination_blob_name}' exists in bucket '{bucket_name}'.")
        else:
            logging.error(f"Blob '{destination_blob_name}' not found after upload!")
    except Exception as e:
        logging.error(f"Failed to upload '{source_file_name}' to GCP: {e}")
# --------------------- NAVIER-STOKES UTILS ----------------------
def central_diff_x(f, dx):
    cdx = np.zeros_like(f)
    cdx[1:-1, 1:-1] = (f[1:-1, 2:] - f[1:-1, 0:-2]) / (2 * dx)
    logging.debug("Computed central difference in x-direction.")
    return cdx

def central_diff_y(f, dy):
    cdy = np.zeros_like(f)
    cdy[1:-1, 1:-1] = (f[2:, 1:-1] - f[0:-2, 1:-1]) / (2 * dy)
    logging.debug("Computed central difference in y-direction.")
    return cdy

def laplace(f, dx, dy):
    lap = np.zeros_like(f)
    lap[1:-1, 1:-1] = (
        f[1:-1, 0:-2] +
        f[1:-1, 2:]   +
        f[0:-2, 1:-1] +
        f[2:, 1:-1]   -
        4 * f[1:-1, 1:-1]
    ) / (dx**2)  # Corrected scaling
    logging.debug("Computed Laplacian.")
    return lap

def open_top_lid_BC_velocity(u, v):
    u[-1, :] = 1.0      # Lid velocity
    v[-1, :] = 0.0      # Lid has no vertical velocity
    logging.debug("Applied open top lid boundary condition for velocity.")
    return u, v

def homogeneous_boundary_condition_velocity(u, v):
    u[0, :] = 0.0       # Bottom boundary
    u[-1, :] = 0.0      # Top boundary (already set by lid)
    u[:, 0] = 0.0       # Left boundary
    u[:, -1] = 0.0      # Right boundary
    v[0, :] = 0.0
    v[-1, :] = 0.0      # Top boundary
    v[:, 0] = 0.0
    v[:, -1] = 0.0
    logging.debug("Applied homogeneous boundary conditions for velocity.")
    return u, v

BOUNDARY_CONDITION = open_top_lid_BC_velocity

# ------------------- NAVIER-STOKES SOLVER -------------------
def run_navier_stokes_solver(sim_params: SimulationParameters) :
    logging.info(f"Starting simulation with parameters:\n{sim_params}")

    # Unpack simulation parameters
    dx, dy = sim_params.dx, sim_params.dy
    T, DT = sim_params.T, sim_params.DT
    Lx, Ly = sim_params.Lx, sim_params.Ly
    Nx, Ny = sim_params.Nx, sim_params.Ny
    N_ITERATIONS = sim_params.N_ITERATIONS
    nu = sim_params.KINEMATIC_VISCOSITY
    rho = sim_params.DENSITY
    do_plot = sim_params.plot
    do_gif = sim_params.gif
    n_poisson_iters = sim_params.N_PRESSURE_POISSON_ITERATIONS

    # Create grid
    xs = np.linspace(0.0, Lx, Nx)
    ys = np.linspace(0.0, Ly, Ny)
    X, Y = np.meshgrid(xs, ys)
    logging.debug(f"Created meshgrid with shape {X.shape}.")

    # Initialize velocity & pressure
    u_prev = np.zeros_like(X)
    v_prev = np.zeros_like(X)
    p_prev = np.zeros_like(X)
    logging.debug("Initialized velocity and pressure fields to zero.")

    # Small initial perturbation (optional)
    center_x, center_y = Nx // 2, Ny // 2
    u_prev[center_y, center_x] = 0.05
    v_prev[center_y, center_x] = 0.05
    logging.debug(f"Introduced perturbation at center ({center_x}, {center_y}) with u=0.05 and v=0.05.")

    # Save initial state
    u_initial = u_prev.copy()
    v_initial = v_prev.copy()
    p_initial = p_prev.copy()

    # For optional GIF
    u_list, v_list, p_list = [], [], []

    # Convergence tolerance for Pressure Poisson
    poisson_tol = 1e-4

    for step in range(1, N_ITERATIONS + 1):
        # Stability check
        if DT > 0.5 * (dx ** 2) / nu:
            logging.error("Time step too large for stability condition (DT>0.5*dx^2/nu).")
            raise ValueError("Time step too large for stability condition (DT>0.5*dx^2/nu).")

        # Derivatives
        dudx = central_diff_x(u_prev, dx)
        dudy = central_diff_y(u_prev, dy)
        dvdx = central_diff_x(v_prev, dx)
        dvdy = central_diff_y(v_prev, dy)
        lapu = laplace(u_prev, dx, dy)
        lapv = laplace(v_prev, dx, dy)
        logging.debug(f"Step {step}: Computed derivatives.")

        # 1) Velocity prediction
        u_star = u_prev + DT * (-(u_prev * dudx + v_prev * dudy) + nu * lapu)
        v_star = v_prev + DT * (-(u_prev * dvdx + v_prev * dvdy) + nu * lapv)
        logging.debug(f"Step {step}: Predicted velocities (u_star, v_star).")

        # Finite checks
        if not (np.isfinite(u_star).all() and np.isfinite(v_star).all()):
            logging.error(f"Numerical instability after velocity prediction at step {step}.")
            break

        # BCs for predicted velocities
        u_star, v_star = homogeneous_boundary_condition_velocity(u_star, v_star)
        u_star, v_star = BOUNDARY_CONDITION(u_star, v_star)
        logging.debug(f"Step {step}: Applied BCs to predicted velocities.")

        # 2) Pressure Poisson
        rhs = (central_diff_x(u_star, dx) + central_diff_y(v_star, dy)) / DT
        logging.debug(f"Step {step}: Computed RHS for pressure Poisson.")

        residual = 1.0
        poisson_step = 0
        while residual > poisson_tol and poisson_step < n_poisson_iters:
            p_new = 0.25 * (
                p_prev[1:-1, :-2] +
                p_prev[1:-1, 2:] +
                p_prev[:-2, 1:-1] +
                p_prev[2:, 1:-1] -
                dx**2 * rhs[1:-1, 1:-1]
            )
            residual = np.linalg.norm(p_new - p_prev[1:-1, 1:-1], ord=2)
            p_prev[1:-1, 1:-1] = p_new

            # Neumann BC for p
            p_prev[:, -1] = p_prev[:, -2]
            p_prev[:, 0] = p_prev[:, 1]
            p_prev[-1, :] = p_prev[-2, :]
            p_prev[0, :] = p_prev[1, :]

            poisson_step += 1
            if poisson_step % 10 == 0 or poisson_step == 1:
                logging.debug(f"Step {step}: Poisson iter {poisson_step}, residual={residual:.6f}")

        if poisson_step == n_poisson_iters and residual > poisson_tol:
            logging.warning(f"Step {step}: Poisson solver not converged (res={residual:.6f}).")

        logging.debug(f"Step {step}: Pressure Poisson solved (res={residual:.6f}).")

        # 3) Velocity correction
        dpdx = central_diff_x(p_prev, dx)
        dpdy = central_diff_y(p_prev, dy)
        u_next = u_star - DT / rho * dpdx
        v_next = v_star - DT / rho * dpdy
        logging.debug(f"Step {step}: Corrected velocities (u_next, v_next).")

        if not (np.isfinite(u_next).all() and np.isfinite(v_next).all()):
            logging.error(f"Numerical instability after velocity correction at step {step}.")
            break

        # BCs for corrected velocities
        u_next, v_next = homogeneous_boundary_condition_velocity(u_next, v_next)
        u_next, v_next = BOUNDARY_CONDITION(u_next, v_next)
        logging.debug(f"Step {step}: Applied BCs to corrected velocities.")

        u_prev, v_prev = u_next, v_next

        # For GIF
        u_list.append(u_next.copy())
        v_list.append(v_next.copy())
        p_list.append(p_prev.copy())

        # Log ranges
        if step % 1000 == 0 or step == 1:
            umin, umax = u_prev.min(), u_prev.max()
            vmin, vmax = v_prev.min(), v_prev.max()
            pmin, pmax = p_prev.min(), p_prev.max()
            logging.info(f"Step {step}/{N_ITERATIONS}: "
                         f"u=[{umin:.4f}, {umax:.4f}], "
                         f"v=[{vmin:.4f}, {vmax:.4f}], "
                         f"p=[{pmin:.4f}, {pmax:.4f}]")

        if not (np.isfinite(u_prev).all() and np.isfinite(v_prev).all() and np.isfinite(p_prev).all()):
            logging.error(f"Numerical instability at step {step}.")
            break

    # Final fields
    p_final = p_prev.copy()
    u_final = u_prev.copy()
    v_final = v_prev.copy()
    logging.debug("Simulation loop completed.")

    if step < N_ITERATIONS:
        logging.warning(f"Simulation ended early at step {step} due to instability.")

    # Plot if completed successfully & data is finite
    if step == N_ITERATIONS and np.all(np.isfinite(u_final)) and np.all(np.isfinite(v_final)) and np.all(np.isfinite(p_final)):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pod_prefix = f"pod-{POD_ID}_"
        plot_filename = f"{RESULTS_DIR}/{pod_prefix}simulation_plot_{timestamp}.png"
        gif_filename = f"{RESULTS_DIR}/{pod_prefix}simulation_animation_{timestamp}.gif"


        if do_plot:
            logging.info("Generating initial & final states plot.")

            # Min/max for color consistency
            p_init_min, p_init_max = p_initial.min(), p_initial.max()
            p_final_min, p_final_max = p_final.min(), p_final.max()
            p_min = min(p_init_min, p_final_min)
            p_max = max(p_init_max, p_final_max)
            logging.debug(f"Pressure scale: [{p_min}, {p_max}]")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=100)

            # INITIAL PLOT
            ax1.set_title("Initial Velocity & Pressure")
            im1 = ax1.imshow(
                p_initial, extent=[0, Lx, 0, Ly],
                origin="lower", cmap="viridis", alpha=0.8,
                vmin=p_min, vmax=p_max
            )
            ax1.streamplot(X, Y, u_initial, v_initial, color="black", density=3.0)
            cbar1 = fig.colorbar(im1, ax=ax1, label="Pressure")
            ax1.set_xlabel("x")
            ax1.set_ylabel("y")
            # Ensure final image fits the axis:
            ax1.set_xlim([0, Lx])
            ax1.set_ylim([0, Ly])

            logging.debug("Plotted initial state.")

            # FINAL PLOT
            ax2.set_title("Final Velocity & Pressure")
            im2 = ax2.imshow(
                p_final, extent=[0, Lx, 0, Ly],
                origin="lower", cmap="viridis", alpha=0.8,
                vmin=p_min, vmax=p_max
            )
            ax2.streamplot(X, Y, u_final, v_final, color="black", density=3.0)
            cbar2 = fig.colorbar(im2, ax=ax2, label="Pressure")
            ax2.set_xlabel("x")
            ax2.set_ylabel("y")
            # Ensure final image fits the axis as well:
            ax2.set_xlim([0, Lx])
            ax2.set_ylim([0, Ly])

            logging.debug("Plotted final state.")

            # Make the figure layout tight but keep axes, labels, ticks
            plt.tight_layout()
            plt.title(f"Simulation Results (Pod {POD_ID})")
            
            plt.savefig(plot_filename)
            logging.info(f"Saved initial/final plot at '{plot_filename}'.")

            # Additional info about saved plot
            logging.debug(f"Plot file '{plot_filename}' shape: {plt.imread(plot_filename).shape}.")

            upload_to_gcp(
                bucket_name=BUCKET_NAME,
                source_file_name=plot_filename,
                destination_blob_name=f"simulation_results/{pod_prefix}simulation_plot_{timestamp}.png",
            )

    # GIF generation if requested
    if do_gif and step == N_ITERATIONS and np.all(np.isfinite(u_final)) and np.all(np.isfinite(v_final)) and np.all(np.isfinite(p_final)):
        logging.info("Generating GIF animation.")
        if len(u_list) == 0 or len(p_list) == 0:
            logging.error("No data for GIF generation.")
        else:
            all_p = np.concatenate([p.ravel() for p in p_list])
            p_min, p_max = all_p.min(), all_p.max()
            logging.debug(f"GIF pressure scale: [{p_min}, {p_max}]")

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.set_xlabel("x")
            ax.set_ylabel("y")

            pressure_im = ax.imshow(
                p_list[0], extent=[0, Lx, 0, Ly],
                origin="lower", cmap="viridis", alpha=0.8,
                vmin=p_min, vmax=p_max
            )
            cb = plt.colorbar(pressure_im, ax=ax, label="Pressure")
            quiver = ax.quiver(
                X[::2, ::2], Y[::2, ::2],
                u_list[0][::2, ::2], v_list[0][::2, ::2],
                scale=1, scale_units="xy", color="black"
            )

            def animate(i):
                quiver.set_UVC(u_list[i][::2, ::2], v_list[i][::2, ::2])
                pressure_im.set_array(p_list[i])
                ax.set_title(f"Velocity & Pressure - Iter {i+1}")
                return quiver, pressure_im

            anim = FuncAnimation(fig, animate, frames=len(u_list), blit=True, interval=100)
            gif_filename = f"{RESULTS_DIR}/simulation_animation_{timestamp}.gif"
            anim.save(gif_filename, writer="pillow")
            logging.info(f"Saved GIF animation at '{gif_filename}'.")

            logging.debug(f"GIF file '{gif_filename}' size: {os.path.getsize(gif_filename)} bytes.")

            upload_to_gcp(
                bucket_name=BUCKET_NAME,
                source_file_name=gif_filename,
                destination_blob_name=f"simulation_results/{pod_prefix}simulation_animation_{timestamp}.gif",
            )

    logging.info("End of simulation.")   
    # ------------------- MAIN FUNCTION -------------------
def main():
    logging.info("Kafka consumer started. Waiting for simulation parameters...")
    for msg in _consumer:
        try:
            param_dict = msg.value
            # Parse into SimulationParameters
            params = SimulationParameters(**param_dict)
            logging.info(f"Received simulation parameters:\n{params}")
            run_navier_stokes_solver(params)
        except Exception as e:
            logging.error(f"Error during simulation: {e}")

if __name__ == "__main__":
    main()