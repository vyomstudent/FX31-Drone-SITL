# Gazebo Harmonic: world, camera and validation boundary

1. First pass the SITL-only telemetry/flight tests.
2. Run `install/03_install_gazebo_harmonic.sh` then `install/04_build_ardupilot_gazebo_plugin.sh`.
3. Run `scripts/run_gazebo_world.sh` in Terminal 1; inspect the scene and resolve any rendering/model errors.
4. Run `scripts/run_gazebo_sitl.sh` in Terminal 2. The upstream ArduPilot plugin documents `sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console`. The included Iris is only an integration stand-in, not the FX31's airframe.
5. Only after the vehicle stays controllable in the scene, work on camera streams and detector datasets.

## World contents

`worlds/fx31_rescue_training_world.sdf` has a simple multi-storey façade/balconies, block obstacles, static person-shaped targets, and orange emissive fire proxies. These objects are deterministic SDF geometry; no online Fuel model downloads are needed. The people are static geometry, not walking/lying animations with realistic appearance. Fire geometry is an RGB-visible cue only, not smoke/flame physics or a physical thermal source.

## Camera

Inspect actual camera/stream topics first:

```bash
gz topic -l | grep -Ei 'camera|streaming'
```

The official Iris-with-gimbal model includes camera/gimbal elements. If the list shows an `.../enable_streaming` topic, copy that *exact* topic path and enable the stream (substitute your discovered path):

```bash
gz topic -t '<EXACT_ENABLE_STREAMING_TOPIC>' -m gz.msgs.Boolean -p 'data: 1'
```

Upstream plugin examples stream GStreamer H.264 on UDP 5600 after enabling. The exact topic path depends on the launched world/model. Then try:

```bash
gst-launch-1.0 -v udpsrc port=5600 caps='application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264' ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false
```

If GStreamer plugins are missing, install the Gazebo-stage packages in the installer and confirm `gstreamer1.0-libav` is present.

## Thermal camera

Gazebo Sim advertises a thermal-camera sensor capability, but a valid feed also needs compatible sensor/render configuration, temperature/material semantics and a topic/output pipeline. The included glowing shapes do not emit validated thermal pixels. Treat thermal integration as a separate experiment and verify it against the installed Gazebo Harmonic version.

## Upstream references

- https://ardupilot.org/dev/docs/sitl-with-gazebo.html
- https://github.com/ArduPilot/ardupilot_gazebo
- https://gazebosim.org/docs/harmonic/sensors/
- https://gazebosim.org/docs/harmonic/install_ubuntu/
