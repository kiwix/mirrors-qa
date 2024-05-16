# Wireguard tester

## Setup

- Create `wg-conf` folder (mounted in compose)
- Copy a mullvad configuration file into `wg-conf/wg0.conf`
- Edit the PreUp and PreDown lines to:

```
PostUp = iptables -t nat -A POSTROUTING -o wg+ -j MASQUERADE
PreDown = iptables -t nat -D POSTROUTING -o wg+ -j MASQUERADE
```

This expects the devices and this the wireguard config files to be named `wgX.conf`.

WARN: wirguard containers modifies that mounted folder so `.conf` files are moved into a `wg-conf/wg_confs` folder.