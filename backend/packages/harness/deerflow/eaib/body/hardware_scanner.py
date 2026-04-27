"""HardwareScanner — auto-detect peripherals and compute resources.

岛叶皮层 (Insular Cortex): scans the host OS for available hardware.

Deliberately dependency-light: only uses stdlib + optional psutil/subprocess.
Never raises — failed probes are logged and returned as unavailable sensors.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deerflow.eaib.body.body_profile import SensorDescriptor

logger = logging.getLogger(__name__)


class HardwareScanner:
    """Scans the current host for available hardware devices and resources."""

    def scan(self) -> list[SensorDescriptor]:
        """Run all probes and return a consolidated sensor list."""
        sensors: list[SensorDescriptor] = []
        sensors.extend(self._scan_video_devices())
        sensors.extend(self._scan_serial_devices())
        sensors.extend(self._scan_lidar_devices())
        sensors.extend(self._scan_audio_devices())
        sensors.extend(self._scan_gpu())
        sensors.extend(self._scan_cpu_ram())
        sensors.extend(self._scan_ros2_topics())
        sensors.extend(self._scan_imu_devices())
        return sensors

    def scan_summary(self) -> dict[str, Any]:
        """Return a structured summary suitable for prompt injection."""
        sensors = self.scan()
        available = [s for s in sensors if s.available]
        by_type: dict[str, list[str]] = {}
        for s in available:
            by_type.setdefault(s.sensor_type, []).append(s.name)
        return {
            "scanned_at": datetime.now(UTC).isoformat(),
            "total_detected": len(available),
            "by_type": by_type,
            "sensors": [s.to_dict() for s in sensors],
        }

    # ------------------------------------------------------------------
    # Video cameras (/dev/video*)
    # ------------------------------------------------------------------

    def _scan_video_devices(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        for p in sorted(Path("/dev").glob("video*")):
            idx_match = re.search(r"\d+", p.name)
            idx = int(idx_match.group()) if idx_match else 0
            sensors.append(
                SensorDescriptor(
                    name=f"camera_{idx}",
                    sensor_type="camera",
                    device_path=str(p),
                    available=p.exists(),
                    extra={"device_index": idx},
                )
            )
        return sensors

    # ------------------------------------------------------------------
    # Serial / USB devices (/dev/ttyUSB*, /dev/ttyACM*)
    # ------------------------------------------------------------------

    def _scan_serial_devices(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        patterns = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyS[0-9]*"]
        for pat in patterns:
            for p in sorted(Path("/dev").glob(pat.lstrip("/dev/"))):
                sensors.append(
                    SensorDescriptor(
                        name=f"serial_{p.name}",
                        sensor_type="serial",
                        device_path=str(p),
                        available=p.exists(),
                    )
                )
        return sensors

    # ------------------------------------------------------------------
    # Lidar devices (common paths + /dev/lidar*)
    # ------------------------------------------------------------------

    def _scan_lidar_devices(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        candidates = list(Path("/dev").glob("lidar*")) + list(Path("/dev").glob("rplidar*"))
        for p in sorted(candidates):
            sensors.append(
                SensorDescriptor(
                    name=f"lidar_{p.name}",
                    sensor_type="lidar",
                    device_path=str(p),
                    available=p.exists(),
                )
            )
        return sensors

    # ------------------------------------------------------------------
    # IMU devices (/dev/iio:device*, /sys/bus/iio/devices/)
    # ------------------------------------------------------------------

    def _scan_imu_devices(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        iio_path = Path("/sys/bus/iio/devices")
        if iio_path.exists():
            for device_dir in sorted(iio_path.iterdir()):
                name_file = device_dir / "name"
                if name_file.exists():
                    try:
                        device_name = name_file.read_text().strip()
                        if any(k in device_name.lower() for k in ("imu", "accel", "gyro", "mpu", "bmi", "lsm")):
                            sensors.append(
                                SensorDescriptor(
                                    name=f"imu_{device_dir.name}",
                                    sensor_type="imu",
                                    device_path=str(device_dir),
                                    available=True,
                                    extra={"chip": device_name},
                                )
                            )
                    except OSError:
                        pass
        return sensors

    # ------------------------------------------------------------------
    # Audio devices (ALSA / PipeWire)
    # ------------------------------------------------------------------

    def _scan_audio_devices(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        # Check for ALSA PCM devices
        for p in sorted(Path("/dev/snd").glob("pcm*")) if Path("/dev/snd").exists() else []:
            is_capture = "c" in p.name
            sensor_type = "microphone" if is_capture else "speaker"
            sensors.append(
                SensorDescriptor(
                    name=f"audio_{p.name}",
                    sensor_type=sensor_type,
                    device_path=str(p),
                    available=True,
                )
            )
        return sensors

    # ------------------------------------------------------------------
    # GPU (nvidia-smi / rocm-smi)
    # ------------------------------------------------------------------

    def _scan_gpu(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        # NVIDIA
        if shutil.which("nvidia-smi"):
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                    timeout=5,
                    text=True,
                ).strip()
                for i, line in enumerate(out.splitlines()):
                    parts = line.split(", ", 1)
                    gpu_name = parts[0].strip()
                    vram = parts[1].strip() if len(parts) > 1 else "unknown"
                    sensors.append(
                        SensorDescriptor(
                            name=f"gpu_{i}",
                            sensor_type="gpu",
                            available=True,
                            extra={"vendor": "nvidia", "model": gpu_name, "vram": vram},
                        )
                    )
            except Exception as e:
                logger.debug("nvidia-smi probe failed: %s", e)
        # AMD ROCm
        if shutil.which("rocm-smi"):
            try:
                out = subprocess.check_output(["rocm-smi", "--showproductname"], timeout=5, text=True)
                for i, line in enumerate(out.splitlines()):
                    if "card" in line.lower():
                        sensors.append(
                            SensorDescriptor(
                                name=f"amd_gpu_{i}",
                                sensor_type="gpu",
                                available=True,
                                extra={"vendor": "amd", "info": line.strip()},
                            )
                        )
            except Exception as e:
                logger.debug("rocm-smi probe failed: %s", e)
        return sensors

    # ------------------------------------------------------------------
    # CPU / RAM (always available)
    # ------------------------------------------------------------------

    def _scan_cpu_ram(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        cpu_extra: dict[str, Any] = {}
        ram_extra: dict[str, Any] = {}

        try:
            import psutil

            cpu_extra = {
                "logical_cores": psutil.cpu_count(logical=True),
                "physical_cores": psutil.cpu_count(logical=False),
                "freq_mhz": round(psutil.cpu_freq().current) if psutil.cpu_freq() else "unknown",
            }
            vm = psutil.virtual_memory()
            ram_extra = {
                "total_gb": round(vm.total / (1024**3), 1),
                "available_gb": round(vm.available / (1024**3), 1),
            }
        except ImportError:
            # Fallback: parse /proc
            try:
                cpuinfo = Path("/proc/cpuinfo").read_text()
                n_procs = cpuinfo.count("processor\t:")
                cpu_extra = {"logical_cores": n_procs}
            except OSError:
                pass
            try:
                meminfo = Path("/proc/meminfo").read_text()
                for line in meminfo.splitlines():
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        ram_extra = {"total_gb": round(kb / (1024**2), 1)}
                    if line.startswith("MemAvailable:"):
                        kb = int(line.split()[1])
                        ram_extra["available_gb"] = round(kb / (1024**2), 1)
            except OSError:
                pass

        sensors.append(SensorDescriptor(name="cpu", sensor_type="cpu", available=True, extra=cpu_extra))
        sensors.append(SensorDescriptor(name="ram", sensor_type="ram", available=True, extra=ram_extra))
        return sensors

    # ------------------------------------------------------------------
    # ROS2 nodes / topics
    # ------------------------------------------------------------------

    def _scan_ros2_topics(self) -> list[SensorDescriptor]:
        sensors: list[SensorDescriptor] = []
        if not shutil.which("ros2"):
            return sensors
        try:
            out = subprocess.check_output(["ros2", "topic", "list"], timeout=5, text=True).strip()
            topics = [t.strip() for t in out.splitlines() if t.strip()]
            for topic in topics:
                ttype = self._classify_ros_topic(topic)
                sensors.append(
                    SensorDescriptor(
                        name=f"ros_{topic.lstrip('/').replace('/', '_')}",
                        sensor_type=ttype,
                        ros_topic=topic,
                        available=True,
                    )
                )
        except Exception as e:
            logger.debug("ROS2 topic scan failed: %s", e)
        return sensors

    def _classify_ros_topic(self, topic: str) -> str:
        topic_lower = topic.lower()
        if any(k in topic_lower for k in ("image", "camera", "rgb", "depth")):
            return "camera"
        if any(k in topic_lower for k in ("scan", "lidar", "pointcloud", "laser")):
            return "lidar"
        if any(k in topic_lower for k in ("imu", "accel", "gyro")):
            return "imu"
        if any(k in topic_lower for k in ("odom", "odometry")):
            return "odometer"
        if any(k in topic_lower for k in ("joint", "motor", "servo")):
            return "joint_encoder"
        if any(k in topic_lower for k in ("gps", "gnss", "fix")):
            return "gps"
        if any(k in topic_lower for k in ("audio", "mic", "sound")):
            return "microphone"
        return "ros_topic"


# Module-level singleton
_scanner: HardwareScanner | None = None


def get_hardware_scanner() -> HardwareScanner:
    global _scanner
    if _scanner is None:
        _scanner = HardwareScanner()
    return _scanner
