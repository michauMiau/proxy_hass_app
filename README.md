# HA Add-on Repository

Add-ons for Home Assistant Supervisor.

## Installing

Add this repository to your Home Assistant:

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FmichauMiau%2Fproxy_hass_app)

Or manually: _Configuration_ → _Add-ons, Backups & Supervisor_ → _Add-on Store_ → _..._ → _Repositories_ → add `https://github.com/michauMiau/proxy_hass_app`.

## Add-ons

- **[HA Ingress Proxy](hass-proxy/README.md)** (`hass-ingress-proxy`). Generic proxy for any local web service. Access NVRs, dashboards, admin panels through HA sidebar without auth redirect issues.
- **[Disk & Battery Watch](disk-battery-watch/README.md)** (`disk-battery-watch`). SMART disk health and battery/UPS status as Home Assistant entities. Parses `smartctl --json` output directly, publishes MQTT discovery entities, and falls back to REST states when no broker is reachable.

