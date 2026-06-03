### 4.1

- Fix nginx startup crash: define `$ingress_path` via `map` directive (was causing "unknown ingress_path variable" error)

### 4.0

- Remove custom proxy_redirect rules — LightNVR doesn't redirect, default behavior is sufficient

### 3.0

- **Major refactor**: Renamed from "Frigate Proxy" to "HA Ingress Proxy" — now generic, not tied to any specific application
- Fix backend auth redirect loops (404 on login pages) by stripping `X-Forwarded-Prefix` header
- Change `proxy_redirect` from `off` to `default` so nginx properly rewrites backend redirects within ingress context
- Updated default server URL to generic placeholder (`http://localhost:8080`)

### 1.6

- Refresh add-on with updated base image and nginx

### 1.5

- Add `proxy_pass_real_ip` option

### 1.4

- Add support for HTTPS upstream servers
  Note the breaking change to configuration which requires the protocol to be
  specified in the server configuration: `http://frigate.local:5000` instead of
  `frigate.local:5000`.

### 1.3

- Set side panel name to Frigate

### 1.2

- Switch to debian base

### 1.1

- Allow access to side panel for non-admins

### 1.0

- Initial release
