# FX31 Codespaces adaptation — evidence and open items

Date: 2026-10-14. Baseline: Copter-4.7.1 (official stable ArduCopter release 2026-09-04).

- The FX31 v1.0.0 SITL kit has been preserved, including synthetic release gate, read-only telemetry, parameter audit and SDF scene variants.
- New `.devcontainer`, bootstrap scripts, separate MAVProxy UDP outputs, private browser read-only dashboard and offline test coverage added.
- Static file checks, bash syntax tests, seeded SDF creation, synthetic release-gate invariants and dashboard unit tests were run in the authoring environment.
- No real ArduPilot SITL executable or Gazebo Harmonic instance was available there. Thus Codespaces build compatibility, successful simulated flight, servo command acknowledgement, GUI rendering, thermal sensor and camera/perception performance are **not verified**.
- The dashboard is a **visual illustrative overlay** using SITL local position, not a Gazebo rendered or spatially calibrated rescue world; it must never be used to validate real collision clearance.
- The optional Gazebo stage may exceed a 2-core free Codespaces machine's CPU or storage.
- The safest next milestone is a successful Codespaces `run_smoke_test.sh` with a human-observed live heartbeat and GPS fix. Next comes a GUIDED/RTL SITL trial; then Gazebo/world/camera integration; only later flight firmware and real airframe testing.
