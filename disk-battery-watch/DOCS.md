# Disk & Battery Watch documentation

Monitors disk S.M.A.R.T. health and battery/UPS status on the host machine and publishes Home Assistant entities. Modern replacement for the 2020-era HDD Tools add-on: structured `smartctl --json` parsing, no cron jobs, no CSV database.

## Entities

Per disk (auto-discovered or configured):

| Entity | Type | Notes |
|---|---|---|
| `binary_sensor.dw_<disk>_health` | problem | `true` when SMART failed, errored, or NVMe critical warning set |
| `sensor.dw_<disk>_temperature` | temperature | °C |
| `sensor.dw_<disk>_power_on_hours` | duration | hours |
| `sensor.dw_<disk>_power_cycles` | count | Power cycle count |
| `sensor.dw_<disk>_reallocated` | sectors | SATA, attribute ID 5 |
| `sensor.dw_<disk>_pending` | sectors | SATA, attribute ID 197 |
| `sensor.dw_<disk>_offline_uncorrectable` | sectors | SATA, attribute ID 198 |
| `sensor.dw_<disk>_reported_uncorrectable` | errors | SATA, attribute ID 187 |
| `sensor.dw_<disk>_reallocated_events` | count | SATA, attribute ID 196 |
| `sensor.dw_<disk>_udma_crc_errors` | errors | SATA, attribute ID 199 |
| `sensor.dw_<disk>_command_timeout` | count | SATA, attribute ID 188 |
| `sensor.dw_<disk>_smart_errors` | count | SATA SMART error log entries |
| `sensor.dw_<disk>_wear` | % | NVMe percentage used |
| `sensor.dw_<disk>_available_spare` | % | NVMe available spare |
| `sensor.dw_<disk>_available_spare_threshold` | % | NVMe spare threshold |
| `sensor.dw_<disk>_critical_warning` | count | NVMe critical warning flags (0 = healthy) |
| `sensor.dw_<disk>_media_errors` | count | NVMe media/data integrity errors |
| `sensor.dw_<disk>_unsafe_shutdowns` | count | NVMe unsafe shutdowns |
| `sensor.dw_<disk>_num_err_log_entries` | count | NVMe error log entries |
| `sensor.dw_<disk>_controller_busy_time` | duration | NVMe controller busy time, minutes |
| `sensor.dw_<disk>_data_written` | data | NVMe host writes, TB |
| `sensor.dw_<disk>_data_read` | data | NVMe host reads, TB |

Entity object ids derive from the kernel device name reported by smartctl, so a disk selected by `/dev/disk/by-id/...` still gets short ids like `dw_sda_*`. ATA-only and NVMe-only sensors are created only when reported data contains the relevant fields.

The health entity carries attributes: device path, model, serial, device type, SMART result, firmware, capacity, rotation rate, form factor, protocol/SATA version and self-test status. With `publish_attributes` enabled it also carries the full ATA SMART attribute registry (id, name, value, worst, threshold, raw) and, for NVMe, the NVMe health log fields. Disks are grouped as MQTT devices by serial (or kernel name), so entities appear under one device in HA.

Per power supply (`/sys/class/power_supply`, `Battery` and `UPS` types only):

| Entity | Type | Notes |
|---|---|---|
| `sensor.dw_bat_<name>_status` | enum | charging, discharging, full, not_charging... |
| `sensor.dw_bat_<name>_level` | battery | % |
| `sensor.dw_bat_<name>_voltage` | voltage | V |
| `sensor.dw_bat_<name>_power` | power | W |
| `sensor.dw_bat_<name>_time_remaining` | duration | seconds, from time_to_full/empty |

## Entity publishing mode

**MQTT discovery** (default) creates registry entities with device classes and statistics. The broker is auto-discovered from Supervisor's MQTT service, so with the Mosquitto core add-on running you do not have to set host, port, username or password at all. Set `mqtt_enabled: false` to skip MQTT entirely.

**REST fallback**: when `mqtt_enabled` is true but the broker is unreachable, entities are pushed through Supervisor's REST API instead (`/api/states`). Those entities have no device classes, MQTT is retried on every cycle, and installing the broker later takes effect without an add-on restart.

Manual options (`mqtt_host`, `mqtt_port`, credentials) act as the fallback when no MQTT service is registered, e.g. an external broker on another machine. Credential fields typed by hand take precedence over service data.

## Configuration

| Option | Default | Description |
|---|---|---|
| `disks` | `[]` (auto) | Explicit device paths, e.g. `/dev/sda`. Empty list auto-discovers SATA and NVMe block devices, skipping virtual devices. |
| `check_interval` | `300` | Seconds between SMART reads. |
| `battery_interval` | `60` | Seconds between power supply reads. |
| `publish_attributes` | `true` | Publish SMART attribute registry and extended disk details as health entity attributes. |
| `mqtt_enabled` | `true` | Use MQTT discovery. |
| `mqtt_host` | `core-mqtt` | Broker host. The MQTT core add-on resolves under this name inside HA OS. |
| `mqtt_port` | `1883` | Broker port (plain TCP, no TLS). |
| `mqtt_username` / `mqtt_password` | empty | Only needed when the broker requires auth. Supervisor treats the password as a secret and masks it everywhere. |

## Caveats

- `smartctl` wakes spun-down disks when reading attributes. If you spin disks down to save power, keep `check_interval` high.
- NVMe wear level is standardized (`percentage_used`); SATA SSD wear reporting is vendor-specific and deliberately not guessed.
- Battery entities only appear when the host actually exposes `/sys/class/power_supply` entries (laptop hosts, UPS-backed hardware). VMs usually have none.
- The add-on needs `SYS_ADMIN` + `SYS_RAWIO` capabilities and host `/dev` visibility to talk to disks directly.
