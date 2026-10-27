# Docker image

| File | Role |
|---|---|
| `Dockerfile` | builds the image from the lock file; base image pinned by digest |
| `environment.yml` | human-readable spec (what we want: Python 3.11, SU2 8.5.0, Gmsh 4.15.2, ...) |
| `environment.lock.txt` | exact package URLs + md5 that the image is built from (322 packages) |

Requires BuildKit (the Dockerfile uses `RUN --mount`). Ubuntu's `docker.io` package does not include it:
install `docker-buildx` (`sudo apt install -y docker-buildx`). Docker Desktop includes it.

Build and check (from the repo root):
```bash
docker build -t nacacfd -f docker/Dockerfile .
scripts/check_image.sh nacacfd
```
Behind a TLS-intercepting proxy add `--secret id=extra_ca,src=<ca-bundle.crt>` to the build.

## Changing versions
1. Edit `environment.yml`.
2. Temporarily build from it (replace the lock file in the Dockerfile `COPY`/`install` lines with `environment.yml`).
3. Export the new lock: `docker run --rm nacacfd micromamba env export -n base --explicit --md5 > docker/environment.lock.txt`
4. Restore the Dockerfile, rebuild from the lock, run `scripts/check_image.sh`, record the change in `docs/agent_log/decisions.md`.

## Known facts (tested 2026-10-27, agent cloud container, 4 vCPU)
- SU2 v8.5.0 "Harrier", Gmsh 4.15.2 (CLI and Python API), Open MPI 5.0.11, Python 3.11.18.
- Image size ~5.3 GB (uncompressed). Large; slimming is possible later if pull time on a VM matters.
- **Not yet tested:** running an actual SU2 case, serial or with MPI (F2).
