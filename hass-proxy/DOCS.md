# HA Ingress Proxy — Documentation

Generic proxy addon for Home Assistant Ingress. Access any local web service through the HA sidebar without auth redirects or login loops.

## Configuration

### Option: `server`

The address of the backend server to proxy to.

Format: `http[s]://host:port`. Examples:
- `http://192.168.1.100:8080`
- `https://nvr.local:443`
- `http://lightnvr:5000`

### Option: `proxy_pass_host`

Whether to pass the original `Host` header to the backend. Default: `true`.

Set to `false` if your backend is behind another proxy (Traefik, Caddy) that needs to see its own hostname for routing.

### Option: `proxy_pass_real_ip`

Whether to pass the client's real IP (`X-Forwarded-For`, `X-Real-IP`) to the backend. Default: `true`.

Set to `false` if your backend only accepts connections from the HA container IP.

## How it works

The addon runs nginx inside a Home Assistant Ingress container. It:
1. Strips the ingress path prefix so backends don't redirect based on `/api/hassio_ingress/...`
2. Rewrites backend redirects (e.g. `Location: /login`) to work correctly within the ingress context
3. Preserves WebSocket upgrades for streaming/video feeds

## Troubleshooting

**Backend redirects to a login page that doesn't exist (404):**
This usually happens when the backend sees the HA ingress path and tries to redirect to its own auth endpoint. The proxy now strips `X-Forwarded-Prefix` so backends treat all requests as root-level — this fixes most 404-on-login issues.

**Backend requires a specific Host header:**
Set `proxy_pass_host: false` if the backend needs to see its original hostname instead of HA's ingress host.

## Support

Issues and PRs welcome on [GitHub](https://github.com/michauMiau/proxy_hass_app).
