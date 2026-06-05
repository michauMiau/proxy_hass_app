### 4.6

- Fix redirect handling: rewrite absolute backend redirects to relative paths so nginx keeps them under the ingress prefix (`/api/hassio_ingress/<token>/...`), fixes double-slash `//` issue and broken login redirects
- Remove `$host` from first `proxy_redirect` argument (was matching client host, not backend internal IP)

### 4.5

- Remove duplicate `proxy_redirect http://$host/ /;` line (was accidentally doubled in v4.4)

### 4.4

- Remove `map $request_uri $ingress_path` from nginx.conf — this custom variable was causing "unknown ingress_path variable" startup crash; `proxy_redirect default` handles everything automatically without it

### 4.3

- Restore `proxy_redirect default` — nginx automatically rewrites backend redirects to match the ingress path, fixing `/login.html` → `/api/hassio_ingress/<token>/login.html` without custom variables or startup crashes

### 4.2

- Remove error_page 404 fallback (login.html JS redirect loop)
- Set `proxy_redirect off` — stop all redirect rewriting, let backend communicate directly with client

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
