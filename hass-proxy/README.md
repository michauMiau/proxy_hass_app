# Home Assistant Add-on: HA Ingress Proxy

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

A generic proxy addon for Home Assistant Ingress. Access any local web service (NVR, dashboards, admin panels) remotely through the HA sidebar without auth redirects or login loops.

This addon does not run any application itself — it only proxies traffic to a backend server you configure.

Is this secure? 
Probably. This app is based off the frigate (insert link to the  original repo) proxy for using frigate through HA. It usss NGINX (pronounced enginks) which is a popular tried and tested Web server/proxy solution.
If i use this with a remote access solution (like Nabu Casa Cloud or Cloudflared) are my Services publicly accesible!?
No, the proxy Goes through the home assistant ingress which is only accesible if you are logged into HA

This ApP was vibecoded, before you leave, not everything is slop here, the original base for this was the frigate proxy ad-don (link here too) which wasn't vibecoded, and the important part NGINX also is not vibecoded, (ai ulepsz repo)
If you're worried about the enviromental impact then, this APP was generated using a self hosted qwen3.6 model run only during the day while the solar panele Werę colleting energy. 
[aarch64-shield]:https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
