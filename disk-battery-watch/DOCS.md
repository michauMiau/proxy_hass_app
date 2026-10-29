# Disk & Battery Watch documentation

Monitors disk S.M.A.R.T. health and battery/UPS status on the host machine and publishes Home Assistant entities. Modern replacement for the 2020-era HDD Tools add-on: structured `smartctl --json` parsing, no cron jobs, no CSV database.

## Entities

Per disk (auto-discovered or configured):

| Entity | Type | Notes |
|---|---|---|
| `binary_sensor.dw_<disk>_health` | problem | `true` when SMART failed, errored, or NVMe critical warning set |
| `sensor.dw_<disk>_temperature` | temperature | °C |
| `sensor.dw_<disk>_power_on_hours` | duration | hours |
| `sensor.dw_<disk>_reallocated` | sectors | SATA only, attribute ID 5 |
| `sensor.dw_<disk>_pending` | sectors | SATA only, attribute ID 197 |
| `sensor.dw_<disk>_smart_errors` | count | SATA SMART error log entries |
| `sensor.dw_<disk>_wear` | % | NVMe only, percentage used |
| `sensor.dw_<disk>_media_errors` | count | NVMe only |

The health entity carries attributes: model, serial, device type, SMART result, firmware and (SATA) the full attribute registry when `publish_attributes` is on. Disks are grouped as MQTT devices, so the entities appear under one device each.

Per power supply (`/sys/class/power_supply`, `Battery` and `UPS` types only):

| Entity | Type | Notes |
|---|---|---|
| `sensor.dw_bat_<name>_status` | enum | charging, discharging, full, not_charging... |
| `sensor.dw_bat_<name>_level` | battery | % |
| `sensor.dw_bat_<name>_voltage` | voltage | V |
| `sensor.dw_bat_<name>_power` | power | W |
| `sensor.dw_bat_<name>_time_remaining` | duration | seconds, from time_to_full/empty |

## Entity publishing mode

**MQTT discovery** (default) creates registry entities with device classes and statistics. Set `mqtt_enabled: false` to skip MQTT entirely.

**REST fallback**: when `mqtt_enabled` is true but the broker is unreachable, entities are pushed through Supervisor's REST API instead (`/api/states`). Those entities have no device classes, so keep MQTT enabled if you want energy/statistics-friendly sensors.

## Configuration

| Option | Default | Description |
|---|---|---|
| `disks` | `[]` (auto) | Explicit device paths, e.g. `/dev/sda`. Empty list auto-discovers SATA and NVMe block devices, skipping virtual devices. |
| `check_interval` | `300` | Seconds between SMART reads. |
| `battery_interval` | `60` | Seconds between power supply reads. |
| `publish_attributes` | `true` | Publish SMART attribute registry on the health entity. |
| `mqtt_enabled` | `true` | Use MQTT discovery. |
| `mqtt_host` | `core-mqtt` | Broker host. The MQTT core add-on resolves under this name inside HA OS. |
| `mqtt_port` | `1883` | Broker port (plain TCP, no TLS). |
| `mqtt_username` / `mqtt_password` | empty | Only needed when the broker requires auth. Supervisor treats the password as a secret and masks it everywhere. |

## Caveats

- `smartctl` wakes spun-down disks when reading attributes. If you spin disks down to save power, keep `check_interval` high.
- NVMe wear level is standardized (`percentage_used`); SATA SSD wear reporting is vendor-specific and deliberately not guessed.
- Battery entities only appear when the host actually exposes `/sys/class/power_supply` entries (laptop hosts, UPS-backed hardware). VMs usually have none.
- The add-on needs `SYS_ADMIN` + `SYS_RAWIO` capabilities and host `/dev` visibility to talk to disks directly.
