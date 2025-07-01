# HPC Adaptation Concepts for Aletheia Platform

This document outlines conceptual approaches for adapting the Aletheia platform's core mathematical computations for High-Performance Computing (HPC) environments. These typically involve using job schedulers like SLURM and parallel programming models like MPI.

The Aletheia platform, with its Celery-based distributed task system, is well-suited for cloud or on-premise clusters. However, traditional HPC systems often have different architectures and software stacks.

## 1. SLURM Submission Script Example

SLURM (Simple Linux Utility for Resource Management) is a common job scheduler on HPC clusters. A SLURM script is used to request resources and submit a batch job.

This example assumes we have a Python script (`hpc_math_runner.py`) that can perform a segment of the ABC conjecture search, perhaps taking a range of numbers or specific parameters as input.

```bash
#!/bin/bash
#SBATCH --job-name=aletheia_abc_search # Job name
#SBATCH --output=aletheia_job_%j.out   # Standard output and error log (%j expands to jobId)
#SBATCH --error=aletheia_job_%j.err
#SBATCH --nodes=4                      # Number of nodes to request
#SBATCH --ntasks-per-node=32           # Number of tasks (cores) per node
#SBATCH --cpus-per-task=1              # Number of CPU cores per task
#SBATCH --mem-per-cpu=2G               # Memory per CPU core
#SBATCH --time=12:00:00                # Wall clock time limit (HH:MM:SS)
#SBATCH --partition=compute            # Specify the partition (queue)

echo "-----------------------------------------------------------------------"
echo "Job ID: $SLURM_JOB_ID"
echo "Run on host: `hostname`"
echo "Operating system: `uname -s`"
echo "Username: $USER"
echo "Started at: `date`"
echo "-----------------------------------------------------------------------"

# Load necessary modules (specific to the HPC environment)
module purge # Clear any inherited modules
module load python/3.11 # Example: Load a specific Python version
module load openmpi/4.1   # Example: Load OpenMPI if using mpi4py
# May need to load modules for GMP, MPFR, MPC if PARI/GP is compiled against system libs
# module load gmp mpfr mpc

# Activate Python virtual environment (if Aletheia is installed in one)
# This path would need to be accessible on the HPC cluster's shared filesystem.
# SOURCE_DIR=/path/to/Aletheia_v3_on_hpc_shared_storage
# VENV_DIR=$SOURCE_DIR/.venv
# source $VENV_DIR/bin/activate
# export PYTHONPATH=$SOURCE_DIR:$PYTHONPATH # Ensure Aletheia modules are findable

# Define parameters for the search job (e.g., ranges, specific algorithm parameters)
# These could be passed as command-line arguments to the Python script
# or managed by a parameter sweep tool.
START_A=1
END_A=1000000
# Other parameters...

# Command to execute the Python script
# If using MPI for parallelism within the script:
# `srun` is SLURM's command to launch parallel tasks.
# `python -m mpi4py your_mpi_script.py` is a common way to run mpi4py scripts.
# The number of processes for MPI would typically match $SLURM_NTASKS or $SLURM_NNODES * $SLURM_NTASKS_PER_NODE.
echo "Launching Aletheia HPC math runner..."
# Example for a non-MPI script, simply run on the first allocated task of the first node:
# python $SOURCE_DIR/scripts/hpc_math_runner.py --start_a $START_A --end_a $END_A

# Example for an MPI script:
# This would launch (nodes * ntasks-per-node) instances of hpc_mpi_runner.py
# Each instance would know its rank and the total size of the MPI communicator.
srun python -u /path/to/Aletheia_v3_on_hpc_shared_storage/scripts/hpc_mpi_runner.py --params_file /path/to/params_for_this_run.json

echo "-----------------------------------------------------------------------"
echo "Finished at: `date`"
echo "-----------------------------------------------------------------------"
```

**Note on `hpc_math_runner.py` or `hpc_mpi_runner.py`:**
This script would be a new Python entry point designed for HPC execution. It would:
-   Import necessary functions from `Aletheia_v3.core.domain` and `Aletheia_v3.core.use_cases`.
-   Parse command-line arguments for its specific work assignment.
-   Perform the calculations.
-   Save results to files in a shared filesystem location, as direct database access might not be available or performant from all compute nodes in an HPC environment. Results would then be batch-ingested into the main Aletheia database.

## 2. MPI for Parallelism (Conceptual Python Snippet with `mpi4py`)

This snippet shows how `mpi4py` could be used within a Python script (`hpc_mpi_runner.py`) to divide a large search space among MPI processes.

```python
# Aletheia_v3/scripts/hpc_mpi_runner.py (Conceptual)
from mpi4py import MPI
import time
import os
import sys

# Assuming Aletheia core modules are in PYTHONPATH
# This might require setting PYTHONPATH=/path/to/Aletheia_v3_parent or careful packaging
try:
    from Aletheia_v3.core.domain import get_quality, ABCTriple, ABCQuality
    from Aletheia_v3.core.use_cases import IntelligentSearchUseCase # Or just parts of it
except ImportError:
    # Fallback if running from a script dir not in default path, adjust as needed
    # This is a common issue in HPC script deployment.
    # Best practice is to install Aletheia as a package on the HPC system.
    # For this example, assume it's runnable.
    print("Error: Could not import Aletheia modules. Ensure PYTHONPATH is set.", file=sys.stderr)
    sys.exit(1)


def perform_search_for_range(a_start, a_end, b_max_factor=1000):
    """
    A simplified search function for a given range of 'a'.
    'b' would iterate up to some factor of 'a' or a fixed limit.
    This is NOT using Bayesian Optimization, just a brute-force style search
    for MPI demonstration.
    """
    hits_found = []
    for a_val in range(a_start, a_end + 1):
        # Determine range for b, ensuring a < b
        # For example, b from a+1 up to a * b_max_factor or some other limit
        for b_val in range(a_val + 1, a_val * b_max_factor +1):
            # In a real scenario, b_val range would be more intelligently chosen
            # or be part of the distributed work unit.
            if b_val <= a_val: continue # Ensure a < b

            # Using the get_quality function from the Aletheia core
            # This will use PARI/GP for GCD and radical.
            quality = get_quality(a_val, b_val)
            if quality > 1.4: # Example threshold
                c_val = a_val + b_val
                triple = ABCTriple(a=a_val, b=b_val, c=c_val)
                hits_found.append(ABCQuality(triple=triple, quality=quality))
                # print(f"Rank {MPI.COMM_WORLD.Get_rank()}: Found hit: a={a_val}, b={b_val}, q={quality:.4f}")
    return hits_found

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size() # Total number of MPI processes

    # Define the total search space for 'a' (example)
    total_a_start = 1
    total_a_end = 100000 # This would be much larger in reality

    # Divide the search space among MPI ranks
    # Each rank gets a chunk of 'a' values to process.
    chunk_size = (total_a_end - total_a_start + 1) // size
    remainder = (total_a_end - total_a_start + 1) % size

    local_a_start = total_a_start + rank * chunk_size
    local_a_end = local_a_start + chunk_size - 1

    # Distribute remainder tasks
    if rank < remainder:
        local_a_start += rank
        local_a_end += (rank + 1)
    else:
        local_a_start += remainder
        local_a_end += remainder

    # Ensure start <= end for the last rank if chunk_size is small
    if local_a_start > total_a_end : local_a_start = total_a_end +1 # make range empty
    if local_a_end > total_a_end : local_a_end = total_a_end
    if local_a_start > local_a_end: # empty range for this rank
        print(f"Rank {rank}: No work assigned (local_a_start={local_a_start}, local_a_end={local_a_end}).")
        local_hits = []
    else:
        print(f"Rank {rank}/{size}: Processing 'a' from {local_a_start} to {local_a_end}")
        start_time = time.time()
        local_hits = perform_search_for_range(local_a_start, local_a_end)
        end_time = time.time()
        print(f"Rank {rank}: Finished in {end_time - start_time:.2f}s. Found {len(local_hits)} hits.")

    # Gather all results at the root process (rank 0)
    all_hits_list = comm.gather(local_hits, root=0)

    if rank == 0:
        print("\n--- All results gathered at root ---")
        final_hits = []
        if all_hits_list:
            for sublist in all_hits_list:
                final_hits.extend(sublist)

        print(f"Total hits found across all processes: {len(final_hits)}")
        # Sort and save to a file (e.g., CSV, JSON)
        final_hits.sort(key=lambda x: x.quality, reverse=True)

        # Example: Save to a timestamped file
        output_filename = f"hpc_results_{os.getenv('SLURM_JOB_ID', 'local')}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_filename, "w") as f:
            f.write(f"# Results from Aletheia HPC run (Job: {os.getenv('SLURM_JOB_ID', 'local')})\n")
            f.write(f"# Total hits: {len(final_hits)}\n")
            for hit in final_hits:
                f.write(f"a={hit.triple.a}, b={hit.triple.b}, c={hit.triple.c}, q={hit.quality:.6f}\n")
        print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    main()
```

**Key Considerations for HPC Adaptation:**

*   **Environment Setup:** Ensuring Python, `cypari2`, `mpi4py`, and Aletheia's core modules are correctly installed and accessible across all compute nodes in the HPC environment is crucial. This often involves working with HPC system administrators.
*   **Data Management:** Reading input parameters and writing large volumes of results efficiently on a shared HPC filesystem needs careful planning. Direct database connections from thousands of compute nodes are usually discouraged; results are typically staged to files and then ingested in batches.
*   **Fault Tolerance:** For very long runs, implementing checkpointing and restart capabilities in the HPC scripts is important.
*   **Algorithm Adaptation:** The Bayesian optimization in `IntelligentSearchUseCase` is inherently sequential. For HPC, one might use many independent Bayesian optimization runs with different starting points/parameters, or adapt the search to a more parallelizable algorithm (like the simple range scan shown in the MPI example, or a parallel genetic algorithm, etc.). The MPI example above uses a brute-force scan for simplicity of demonstrating parallelism, not an intelligent search.

This document provides a starting point for thinking about how Aletheia's mathematical core could be leveraged in traditional HPC settings.
```
