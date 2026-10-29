#!/usr/bin/env python3
"""Disk & Battery Watch — modern SMART + power-supply monitoring for HA add-ons.

Replaces the 2020-era grep/awk/cron approach with structured parsing:
smartctl --json output instead of text scraping, /sys/class/power_supply for
battery/UPS status, and MQTT discovery entities (proper entity registry,
device classes, device grouping) with a REST /api/states fallback when no
MQTT broker is configured. Python standard library only — no pip installs.
"""

import json
import os
import re
import socket
import subprocess
import time
import urllib.request

OPTIONS_PATH = os.environ.get("DISK_WATCH_OPTIONS", "/data/options.json")
POWER_SUPPLY_ROOT = os.environ.get(
    "DISK_WATCH_POWER_SUPPLY_ROOT", "/sys/class/power_supply"
)
BLOCK_ROOT = os.environ.get("DISK_WATCH_BLOCK_ROOT", "/sys/block")
PREFIX = "hass_disk_watch"
HASS_API = os.environ.get("HASS_API", "http://supervisor/core/api")

_SKIP_BLOCK_PREFIXES = ("sr", "sg", "loop", "ram", "zram", "dm-", "md")


def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def sanitize(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def load_options():
    try:
        with open(OPTIONS_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError) as err:
        log(f"Options unavailable ({err}), using defaults")
        raw = {}

    def as_int(key, default, low, high):
        try:
            return max(low, min(high, int(raw.get(key, default))))
        except (TypeError, ValueError):
            return default

    return {
        "disks": raw.get("disks") or [],
        "check_interval": as_int("check_interval", 300, 30, 86400),
        "battery_interval": as_int("battery_interval", 60, 10, 3600),
        "publish_attributes": bool(raw.get("publish_attributes", True)),
        "mqtt_enabled": bool(raw.get("mqtt_enabled", True)),
        "mqtt_host": raw.get("mqtt_host") or "core-mqtt",
        "mqtt_port": as_int("mqtt_port", 1883, 1, 65535),
        "mqtt_username": raw.get("mqtt_username") or "",
        "mqtt_password": raw.get("mqtt_password") or "",
    }


def discover_disks(options):
    if options["disks"]:
        return options["disks"]
    disks = []
    try:
        for entry in sorted(os.listdir(BLOCK_ROOT)):
            if not (entry.startswith("sd") or entry.startswith("nvme")):
                continue
            if entry.startswith(_SKIP_BLOCK_PREFIXES):
                continue
            disks.append(f"/dev/{entry}")
    except OSError as err:
        log(f"Block scan failed: {err}")
    return disks


def smartctl_json(device):
    try:
        proc = subprocess.run(
            ["smartctl", "--json=c", "-a", device],
            capture_output=True,
            text=True,
            timeout=45,
        )
    except subprocess.TimeoutExpired:
        return {"_error": "smartctl timed out after 45 s"}
    except OSError as err:
        return {"_error": f"smartctl could not run: {err}"}
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"_error": f"smartctl exit {proc.returncode}, no JSON output"}


def find_attribute(data, attribute_id):
    for attr in data.get("ata_smart_attributes", {}).get("registry", []):
        if attr.get("id") == attribute_id:
            return attr
    return None


def raw_value(attr):
    if not attr:
        return None
    raw = attr.get("raw")
    if isinstance(raw, dict):
        return raw.get("value")
    return raw


def build_disk_entities(device, data, options):
    key = sanitize(os.path.basename(device))
    serial = (data.get("serial_number") or "").strip()
    model = (data.get("model_name") or "").strip()
    ident = sanitize(serial) or key
    display = model or os.path.basename(device)
    device_info = {"identifiers": [f"disk-watch-{ident}"], "name": display}
    if model:
        device_info["model"] = model
    if serial:
        device_info["serial_number"] = serial

    nvme = data.get("nvme_smart_health_information_log") or {}
    device_type = data.get("disk_info", {}).get("device_type", "")

    error = data.get("_error")
    if error:
        problem, result = True, "ERROR"
    elif nvme:
        warning = int(nvme.get("critical_warning", 0))
        spare = nvme.get("available_spare")
        threshold = nvme.get("available_spare_threshold")
        problem = bool(warning) or (
            spare is not None
            and threshold is not None
            and spare <= threshold
        )
        result = "FAILED" if problem else "PASSED"
    elif data.get("smart_status") is not None:
        problem = not bool(data["smart_status"].get("passed"))
        result = "FAILED" if problem else "PASSED"
    elif data.get("smart_supported") is False:
        problem, result = False, "NOT SUPPORTED"
    elif data.get("smart_enabled") is False:
        problem, result = False, "DISABLED"
    else:
        problem, result = False, "UNKNOWN"

    entities = []

    def add(domain, field, label, value, extra=None, attrs=None):
        if value is None:
            return
        obj = f"dw_{key}_{field}"
        config = {
            "name": f"{display} {label}",
            "unique_id": f"disk-watch-{ident}-{field}",
            "state_topic": f"{PREFIX}/state/{obj}",
            "device": device_info,
        }
        if extra:
            config.update(extra)
        entities.append(
            {
                "domain": domain,
                "obj": obj,
                "value": value,
                "config": config,
                "attrs": attrs,
            }
        )

    health_attrs = None
    health_topic = None
    if options["publish_attributes"]:
        health_attrs = {
            "device_path": device,
            "model": model,
            "serial": serial,
            "device_type": device_type,
            "smart_result": result,
            "firmware": data.get("firmware_version"),
        }
        health_topic = f"{PREFIX}/attrs/{key}"
        registry = [
            {
                "name": attr.get("name"),
                "value": attr.get("value"),
                "worst": attr.get("worst"),
                "thresh": attr.get("thresh"),
                "raw": (attr.get("raw") or {}).get("string")
                if isinstance(attr.get("raw"), dict)
                else attr.get("raw"),
            }
            for attr in data.get("ata_smart_attributes", {}).get("registry", [])
        ]
        if registry:
            health_attrs["smart_attributes"] = registry
    health_extra = {
        "device_class": "problem",
        "payload_on": "true",
        "payload_off": "false",
    }
    if health_topic:
        health_extra["json_attributes_topic"] = health_topic
    add(
        "binary_sensor",
        "health",
        "SMART health",
        "true" if problem else "false",
        extra=health_extra,
        attrs=health_attrs,
    )

    temperature = (data.get("temperature") or {}).get("current")
    if temperature is None:
        temperature = nvme.get("temperature")
    add(
        "sensor",
        "temperature",
        "temperature",
        temperature,
        extra={
            "device_class": "temperature",
            "unit_of_measurement": "°C",
            "state_class": "measurement",
        },
    )

    power_on_hours = (data.get("power_on_time") or {}).get("hours")
    if power_on_hours is None:
        power_on_hours = nvme.get("power_on_hours")
    add(
        "sensor",
        "power_on_hours",
        "power-on hours",
        power_on_hours,
        extra={"device_class": "duration", "unit_of_measurement": "h"},
    )

    if nvme:
        add(
            "sensor",
            "wear",
            "wear level",
            nvme.get("percentage_used"),
            extra={"unit_of_measurement": "%", "state_class": "measurement"},
        )
        add(
            "sensor",
            "media_errors",
            "media errors",
            nvme.get("media_errors", 0),
            extra={"state_class": "measurement"},
        )
    else:
        registry = data.get("ata_smart_attributes", {}).get("registry")
        if registry:
            add(
                "sensor",
                "reallocated",
                "reallocated sectors",
                raw_value(find_attribute(data, 5)),
                extra={"unit_of_measurement": "sectors", "state_class": "measurement"},
            )
            add(
                "sensor",
                "pending",
                "unresolved sectors",
                raw_value(find_attribute(data, 197)),
                extra={"unit_of_measurement": "sectors", "state_class": "measurement"},
            )
            errors = (
                data.get("ata_smart_error_log", {}).get("summary", {}).get("count")
            )
            add(
                "sensor",
                "smart_errors",
                "SMART error count",
                errors if errors is not None else 0,
                extra={"unit_of_measurement": "errors", "state_class": "measurement"},
            )

    return entities


def read_sysfs(base, name):
    try:
        with open(os.path.join(base, name), "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def sysfs_int(base, name):
    raw = read_sysfs(base, name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def build_battery_entities(supply_name):
    base = os.path.join(POWER_SUPPLY_ROOT, supply_name)
    supply_type = read_sysfs(base, "type")
    if supply_type not in ("Battery", "UPS"):
        return []

    key = sanitize(supply_name)
    display = f"{supply_type} {supply_name}"
    device_info = {"identifiers": [f"battery-watch-{key}"], "name": display}

    entities = []

    def add(field, label, value, extra=None, attrs=None):
        if value is None:
            return
        obj = f"dw_bat_{key}_{field}"
        entities.append(
            {
                "domain": "sensor",
                "obj": obj,
                "value": value,
                "config": {
                    "name": f"{display} {label}",
                    "unique_id": f"battery-watch-{key}-{field}",
                    "state_topic": f"{PREFIX}/state/{obj}",
                    "device": device_info,
                    **(extra or {}),
                },
                "attrs": attrs,
            }
        )

    status = (read_sysfs(base, "status") or "unknown").lower().replace("-", "_")
    add(
        "status",
        "status",
        status,
        extra={"device_class": "enum"},
        attrs={"supply_type": supply_type, "sysfs_path": base},
    )

    capacity = sysfs_int(base, "capacity")
    add(
        "level",
        "level",
        capacity,
        extra={
            "device_class": "battery",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        },
    )

    voltage_raw = sysfs_int(base, "voltage_now")
    voltage = round(voltage_raw / 1_000_000, 2) if voltage_raw is not None else None
    add(
        "voltage",
        "voltage",
        voltage,
        extra={
            "device_class": "voltage",
            "unit_of_measurement": "V",
            "state_class": "measurement",
        },
    )

    power_raw = sysfs_int(base, "power_now")
    power = round(power_raw / 1000, 1) if power_raw is not None else None
    add(
        "power",
        "power",
        power,
        extra={
            "device_class": "power",
            "unit_of_measurement": "W",
            "state_class": "measurement",
        },
    )

    seconds = None
    if status == "discharging":
        seconds = sysfs_int(base, "time_to_empty_now")
    elif status == "charging":
        seconds = sysfs_int(base, "time_to_full_now")
    if seconds is not None and seconds <= 0:
        seconds = None
    add(
        "time_remaining",
        "time remaining",
        seconds,
        extra={
            "device_class": "duration",
            "unit_of_measurement": "s",
            "state_class": "measurement",
        },
    )

    return entities


def _mqtt_varint(length):
    out = bytearray()
    while True:
        byte = length & 0x7F
        length >>= 7
        if length:
            byte |= 0x80
        out.append(byte)
        if not length:
            return out


def _recv_exact(sock, count):
    buf = b""
    while len(buf) < count:
        chunk = sock.recv(count - len(buf))
        if not chunk:
            raise RuntimeError("MQTT connection closed early")
        buf += chunk
    return buf


def mqtt_publish(options, messages):
    """Publish (topic, payload, retain) tuples over one MQTT 3.1.1 session, QoS 0."""
    sock = socket.create_connection(
        (options["mqtt_host"], options["mqtt_port"]), timeout=10
    )
    try:
        flags = 0
        connect_payload = bytearray()

        def add_string(value):
            encoded = value.encode("utf-8")
            connect_payload.extend(len(encoded).to_bytes(2, "big") + encoded)

        add_string(f"hass-disk-watch-{os.getpid()}")
        if options["mqtt_username"]:
            flags |= 0x80
            add_string(options["mqtt_username"])
        if options["mqtt_password"]:
            flags |= 0x40
            add_string(options["mqtt_password"])

        variable = b"\x00\x04MQTT\x04" + bytes([flags, 30, 0]) + connect_payload
        sock.sendall(b"\x10" + _mqtt_varint(len(variable)) + variable)

        connack = _recv_exact(sock, 4)  # header, length, session flags, reason code
        if connack[0] != 0x20 or connack[3] != 0x00:
            raise RuntimeError(f"MQTT CONNACK refused, code {connack[3]}")

        for topic, payload, retain in messages:
            topic_bytes = topic.encode("utf-8")
            payload_bytes = payload.encode("utf-8")
            variable = len(topic_bytes).to_bytes(2, "big") + topic_bytes + payload_bytes
            packet_type = 0x20 | (0x01 if retain else 0x00)
            sock.sendall(bytes([packet_type]) + _mqtt_varint(len(variable)) + variable)
    finally:
        sock.close()


def rest_set_state(entity_id, state, attributes):
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise RuntimeError("SUPERVISOR_TOKEN is not available")
    request = urllib.request.Request(
        f"{HASS_API}/states/{entity_id}",
        data=json.dumps(
            {"entity_id": entity_id, "state": state, "attributes": attributes}
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    urllib.request.urlopen(request, timeout=10)


class Publisher:
    def __init__(self, options):
        self.options = options
        self.mode = "mqtt" if options["mqtt_enabled"] else "rest"
        self.published_configs = set()

    def publish(self, entities):
        if self.mode == "mqtt":
            messages = []
            for entity in entities:
                obj = entity["obj"]
                if obj not in self.published_configs:
                    messages.append(
                        (
                            f"homeassistant/{entity['domain']}/{obj}/config",
                            json.dumps(entity["config"]),
                            True,
                        )
                    )
                    self.published_configs.add(obj)
                attrs_topic = entity["config"].get("json_attributes_topic")
                if attrs_topic and entity.get("attrs") is not None:
                    messages.append(
                        (attrs_topic, json.dumps(entity["attrs"]), True)
                    )
                messages.append((entity["config"]["state_topic"], str(entity["value"]), True))
            try:
                mqtt_publish(self.options, messages)
                return
            except (OSError, RuntimeError) as err:
                log(f"MQTT publish failed ({err}), switching to REST states")
                self.mode = "rest"

        failures = 0
        for entity in entities:
            entity_id = f"{entity['domain']}.{entity['obj']}"
            try:
                rest_set_state(entity_id, str(entity["value"]), entity.get("attrs") or {})
            except (OSError, RuntimeError) as err:
                if failures == 0:
                    log(f"REST state failed for {entity_id}: {err}")
                failures += 1
        if failures > 1:
            log(f"{failures - 1} more REST states failed this cycle")


def main():
    options = load_options()
    log(
        f"Disk & Battery Watch started (disks={options['disks'] or 'auto'}, "
        f"smart every {options['check_interval']} s, battery every {options['battery_interval']} s, "
        f"entity mode={'mqtt' if options['mqtt_enabled'] else 'rest'})"
    )
    publisher = Publisher(options)
    now = time.monotonic()
    next_disk = now
    next_battery = now

    while True:
        entities = []

        if time.monotonic() >= next_disk:
            try:
                disks = discover_disks(options)
                if not disks:
                    log("No block devices found for SMART monitoring")
                for device in disks:
                    entities.extend(
                        build_disk_entities(device, smartctl_json(device), options)
                    )
            except Exception as err:  # noqa: BLE001 — keep the loop alive
                log(f"Disk check failed: {err}")
            next_disk = time.monotonic() + options["check_interval"]

        if time.monotonic() >= next_battery:
            try:
                for supply_name in sorted(os.listdir(POWER_SUPPLY_ROOT)):
                    entities.extend(build_battery_entities(supply_name))
            except OSError as err:
                log(f"Power supply scan failed: {err}")
            next_battery = time.monotonic() + options["battery_interval"]

        if entities:
            publisher.publish(entities)

        delay = min(next_disk, next_battery) - time.monotonic()
        time.sleep(max(1.0, min(delay, 300.0)))


if __name__ == "__main__":
    main()
