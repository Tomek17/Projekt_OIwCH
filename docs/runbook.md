# Runbook: run an experiment on any Linux VM

Status: **written, not tested** (the image does not exist yet; F1/F6).

1. Start a Linux VM (Ubuntu 24.04 recommended) with N vCPUs. Note provider, instance type, price per hour.
2. Install Docker: `sudo apt update && sudo apt install -y docker.io git && sudo usermod -aG docker $USER`,
   then log out and in again.
3. Get the code: `git clone https://github.com/Tomek17/Projekt_OIwCH.git && cd Projekt_OIwCH`
4. Build the image: `docker build -t nacacfd -f docker/Dockerfile .`
5. Run: `docker run --rm -v "$PWD":/work -w /work nacacfd nacacfd run experiments/<experiment>.yaml`
6. Copy back `runs/<experiment>/` (e.g. `scp -r` or commit the small JSON/CSV files).
7. **Stop/delete the VM** and write the cost and wall time into `docs/agent_log/metrics.md`.

Local WSL2 (student's laptop): same steps 2-6 inside Ubuntu; keep the repo under `~`, not `/mnt/c`.
