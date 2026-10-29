### 1.0.0

- Initial release: modern replacement for the 2020-era HDD Tools approach
- Structured `smartctl --json` parsing instead of grep/awk text scraping
- Multi-disk support with automatic block-device discovery (or explicit `disks` list)
- NVMe health log support: wear level, media errors, critical warning
- SATA support: reallocated / unresolved sector counts, SMART error log count, full attribute registry in attributes
- Battery and UPS status from `/sys/class/power_supply` (status, level, voltage, power, time remaining)
- MQTT discovery entities (device grouping, device classes, problem binary sensor) with automatic REST fallback when no broker is reachable
- s6 long-run service, no cron, no CSV database
