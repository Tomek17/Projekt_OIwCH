# syntax=docker/dockerfile:1
# Image with SU2 + Gmsh + Python scientific stack.
# Build from the repo root:
#   docker build -t nacacfd -f docker/Dockerfile .
# Behind a TLS-intercepting proxy (e.g. the Claude Code cloud container), pass the proxy CA as a build secret;
# it is used only during the build and is not stored in the image:
#   docker build --secret id=extra_ca,src=/path/to/ca-bundle.crt -t nacacfd -f docker/Dockerfile .
FROM mambaorg/micromamba:2.3.0@sha256:d008b2611d604c4e0c8e3652c7f9dca7cd65a103d68a2db30112702078a45c7a

# The image is built from the explicit lock file (exact package URLs + md5), not from environment.yml.
# To change versions: edit environment.yml, rebuild with it, re-export the lock (see docker/README.md).
COPY --chown=$MAMBA_USER:$MAMBA_USER docker/environment.lock.txt /tmp/environment.lock.txt
RUN --mount=type=secret,id=extra_ca,mode=0444 \
    if [ -f /run/secrets/extra_ca ]; then SSL="--ssl-verify /run/secrets/extra_ca"; else SSL=""; fi && \
    micromamba install -y -n base $SSL -f /tmp/environment.lock.txt && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /opt/nacacfd
COPY --chown=$MAMBA_USER:$MAMBA_USER pyproject.toml ./
COPY --chown=$MAMBA_USER:$MAMBA_USER src ./src
# No network needed: setuptools comes from the conda environment.
RUN pip install --no-deps --no-build-isolation -e .

# When the repository is mounted at /work, its code takes precedence over the copy baked into the image,
# so the git hash recorded for a run matches the code that ran. Without a mount the baked copy is used.
ENV PYTHONPATH=/work/src
WORKDIR /work
