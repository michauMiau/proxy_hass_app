### 1.0.3

- MQTT broker auto-discovery via Supervisor services (`services: mqtt:want` + `GET /services/mqtt`). Mosquitto registers the broker host, port and credentials as `mqtt:provide`, so `mqtt_host` can stay at its default and no credentials need typing by hand
- MQTT failures no longer stick forever in REST mode; the REST states ship each cycle while MQTT retries, so installing the broker later needs no add-on restart
- Config-only MQTT hint logs throttled to the first cycle and every tenth failure

### 1.0.2

- `hassio_api: true` added — the Supervisor proxy rejects REST calls from add-ons without this permission (401 Unauthorized, source: api/proxy.py `_check_access` requires `access_homeassistant_api`)
- Entity object ids now follow the kernel device name, so `disks` entries under `/dev/disk/by-id` give short ids like `dw_sda_*`
- Unresolvable MQTT host logs a broker hint instead of a bare errno, then falls back to REST

### 1.0.1

- s6 service type fixed: `longrun`, not `long-run` (Supervisor caches the built image by version, so the broken first build kept running after the repo pull)
- `mqtt_password` uses the Supervisor `password` schema type, so the value is masked in the UI, API and logs

### 1.0.0

- Initial release: modern replacement for the 2020-era HDD Tools approach
- Structured `smartctl --json` parsing instead of grep/awk text scraping
- Multi-disk support with automatic block-device discovery (or explicit `disks` list)
- NVMe health log support: wear level, media errors, critical warning
- SATA support: reallocated / unresolved sector counts, SMART error log count, full attribute registry in attributes
- Battery and UPS status from `/sys/class/power_supply` (status, level, voltage, power, time remaining)
- MQTT discovery entities (device grouping, device classes, problem binary sensor) with automatic REST fallback when no broker is reachable
- s6 long-run service, no cron, no CSV database
