# Home Assistant Add-on: HA Ingress Proxy

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

A generic proxy add-on for Home Assistant Ingress. Access any local web service (NVR, dashboards, admin panels) remotely through the HA sidebar without auth redirects or login loops.

## What is this?

This add-on does not run any application itself, it only proxies traffic to a backend server you configure via NGINX (pronounced enginks). It was based on [Frigate's proxy add-on](https://github.com/blakeblackshear/frigate/tree/master/docker/frigate-proxy), which provides the same pattern for accessing Frigate's web UI through Home Assistant.

## Security

**Is this secure?** Yes, probably

- The proxy runs inside Home Assistant's Ingress system, which is only accessible when you are logged into HA.
- If you use remote access (Nabu Casa Cloud, Cloudflare Tunnel / `cloudflared`, or any other method), the proxy panel remains protected by your HA login. You cannot reach it without being authenticated in Home Assistant first.
- NGINX is a battle-tested web server/proxy — this add-on uses it for what it does best: reverse-proxying traffic to a backend container on the Supervisor network (`172.30.32.x`).

## Trusted networks / CIDR gotcha

If your backend service (LightNVR, Frigate, Synology DSM, whatever) shows a login page or 404 even though you're logged into Home Assistant, this is usually the problem.

When traffic goes through HA Ingress, it comes from `172.30.32.x` — that's Docker's internal network for addons. To your backend service, that looks like an unknown IP trying to access protected resources. Most NVRs and dashboards have a "trusted networks" or "allowed CIDR" setting and they reject anything outside their LAN range.

**Fix:** add `172.30.0.0/16` (or at least `172.30.32.0/24`) to the trusted networks / allowed IPs list in your backend service's settings. For LightNVR that's in the network configuration section. For Frigate it's under `trusted_networks` in `config.yaml`.

If your service doesn't have a trusted networks setting and you're desperate, you can set `host_network: true` in this addon's config. That gives the proxy a real LAN IP instead of a Docker one, so the backend sees it as "local traffic". Less secure but it works.

This app was vibecoded. Before you leave, not everything is slop here, the original base for this was the Frigate proxy add-on (link above) which wasn't vibecoded, and the important part NGINX also isn't vibecoded.

If you're worried about the environmental impact then, this app was generated using a self-hosted Qwen3.6 model run only during the day while the solar panels were collecting energy. ☀️🐈

## Configuration

See the [configuration documentation](CONFIGURATION.md) for setup instructions and available options.

## License

This project is licensed under the MIT License — see [LICENSE](../LICENSE).

## Credits
Shoutout to https://pictogrammers.com/library/ for the icons
Props to frigate for the original addon

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
