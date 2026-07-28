# Shared env setup for H100 runs: ssrm_hopper has vllm 0.19.0 with FA3 sm_90.
# Source this after setting CUDA_VISIBLE_DEVICES.
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ssrm_hopper
# login env puts /usr/local/cuda/lib64 (cuBLAS 12.9) on LD_LIBRARY_PATH which
# shadows torch's bundled cuBLAS 12.8 -> replace with conda lib only
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib
