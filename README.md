# Home Assistant Ingress Proxy Add-ons

Collection of Home Assistant add-ons for proxying local web services through HA Ingress. Access any local dashboard, NVR, or admin panel remotely via the HA sidebar — without auth redirects or login loops.

## Installing

Add this repository to your Home Assistant:

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FmichauMiau%2Fproxy_hass_app)

Or manually: _Configuration_ → _Add-ons, Backups & Supervisor_ → _Add-on Store_ → _..._ → _Repositories_ → add `https://github.com/michauMiau/proxy_hass_app`.

## Add-ons

- **[HA Ingress Proxy](hass-proxy/README.md)** — Generic proxy for any local web service. Access NVRs, dashboards, admin panels through HA sidebar without auth redirect issues.
