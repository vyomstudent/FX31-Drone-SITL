#!/usr/bin/env bash
set -Eeuo pipefail
if ! grep -qi ubuntu /etc/os-release; then echo 'ERROR: Ubuntu is required.' >&2; exit 2; fi
. /etc/os-release
if [[ "${VERSION_ID:-}" != "22.04" && "${VERSION_ID:-}" != "24.04" ]]; then echo "ERROR: expected Ubuntu 22.04/24.04; found ${VERSION_ID:-unknown}." >&2; exit 3; fi
sudo apt-get update
sudo apt-get install -y curl lsb-release gnupg
sudo curl -fsSL https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list >/dev/null
sudo apt-get update
sudo apt-get install -y gz-harmonic libgz-sim8-dev rapidjson-dev libopencv-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl
gz sim --versions
printf '\nPASS: Gazebo Harmonic installed. Smoke test: gz sim -v4 -r shapes.sdf\n'
