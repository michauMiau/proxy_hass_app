# Disk & Battery Watch

SMART disk health and battery/UPS status for Home Assistant, as registry entities.

A modern take on [HDD Tools](https://github.com/Draggon/hassio-hdd-tools): `smartctl --json` structured parsing instead of text scraping, an s6 service instead of cron, NVMe health logs, and MQTT discovery entities with device grouping.

## Requirements

- Home Assistant 2024.10+ (enum and duration device classes)
- MQTT integration if you want discovery entities (the REST fallback works without it, minus device classes)
- A host with real disks attached. The add-on reads SMART via `smartctl`
