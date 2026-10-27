# Image with SU2 + Gmsh + Python scientific stack.
# Status: DRAFT, written but NOT built yet (F1). Build from the repo root:
#   docker build -t nacacfd -f docker/Dockerfile .
# TODO F1: pin the base image by digest; check whether conda-forge su2 is built with MPI
#          (needed for multi-core runs of one case); otherwise build SU2 from tag v8.5.0.
FROM mambaorg/micromamba:2.3.0

COPY --chown=$MAMBA_USER:$MAMBA_USER docker/environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /opt/nacacfd
COPY --chown=$MAMBA_USER:$MAMBA_USER pyproject.toml ./
COPY --chown=$MAMBA_USER:$MAMBA_USER src ./src
RUN pip install --no-deps -e .

WORKDIR /work
