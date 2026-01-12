# ATEM Network Access Setup

This document explains how to set up network access to the ATEM Mini from your Mac (or other computers on the WiFi network) when the ATEM is connected to the Raspberry Pi via Ethernet.

## Network Topology

```
[Mac/Computer] <--WiFi--> [Router] <--WiFi--> [Raspberry Pi] <--Ethernet--> [ATEM Mini]
   192.168.1.x              192.168.1.1        192.168.1.91      192.168.100.2
                                               192.168.100.3
```

## Why This Is Needed

The ATEM Mini uses **UDP port 9910** for control communication. When the ATEM is connected directly to the Pi's Ethernet port, it's on a different subnet (192.168.100.x) than your WiFi network (192.168.1.x). 

To access the ATEM from your Mac, we need to set up **IP forwarding** on the Pi to bridge these two networks.

## Installation Steps

### 1. Install iptables-persistent

```bash
sudo apt-get update
sudo apt-get install -y iptables-persistent
```

When prompted to save current rules, select **Yes** for both IPv4 and IPv6.

### 2. Enable IP Forwarding

```bash
# Enable immediately
sudo sysctl -w net.ipv4.ip_forward=1

# Make permanent (survives reboot)
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
```

### 3. Set Up iptables Rules for ATEM (UDP Port 9910)

**IMPORTANT:** The ATEM uses **UDP**, not TCP!

```bash
# Forward UDP port 9910 from WiFi to ATEM
sudo iptables -t nat -A PREROUTING -i wlan0 -p udp --dport 9910 -j DNAT --to-destination 192.168.100.2:9910
sudo iptables -t nat -A POSTROUTING -o eth0 -p udp --dport 9910 -d 192.168.100.2 -j MASQUERADE
sudo iptables -A FORWARD -i wlan0 -o eth0 -p udp --dport 9910 -d 192.168.100.2 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan0 -p udp --sport 9910 -s 192.168.100.2 -j ACCEPT
```

### 4. Save iptables Rules

```bash
sudo netfilter-persistent save
```

This saves the rules to `/etc/iptables/rules.v4` so they persist across reboots.

## Verification

### Test from the Pi

```bash
# Verify ATEM is reachable
ping -c 2 192.168.100.2

# Check iptables rules
sudo iptables -t nat -L -n -v
```

### Test from Your Mac

```bash
# Test UDP port (requires netcat)
nc -u -z -v 192.168.1.91 9910
```

## Using ATEM Software Control

1. Download and install **ATEM Software Control** from Blackmagic Design
2. Launch the application
3. Connect to: **192.168.1.91** (the Pi's WiFi IP address)
4. The connection will be forwarded to the ATEM at 192.168.100.2

## Automated Setup Script

For easy deployment to new devices, use the included script:

```bash
chmod +x setup_atem_forwarding.sh
sudo ./setup_atem_forwarding.sh
```

**Note:** The script in the repository currently has TCP rules. Update it to use UDP as shown above.

## Troubleshooting

### Connection Refused

- Verify the ATEM is powered on
- Check that the Ethernet cable is connected
- Verify the Pi can ping the ATEM: `ping 192.168.100.2`

### Rules Not Persisting After Reboot

- Ensure iptables-persistent is installed
- Run `sudo netfilter-persistent save` after adding rules
- Check `/etc/iptables/rules.v4` exists and contains your rules

### Wrong Protocol

- The ATEM uses **UDP port 9910**, not TCP
- If you accidentally set up TCP rules, remove them:
  ```bash
  sudo iptables -t nat -D PREROUTING -i wlan0 -p tcp --dport 9910 -j DNAT --to-destination 192.168.100.2:9910
  sudo iptables -t nat -D POSTROUTING -o eth0 -p tcp --dport 9910 -d 192.168.100.2 -j MASQUERADE
  sudo iptables -D FORWARD -i wlan0 -o eth0 -p tcp --dport 9910 -d 192.168.100.2 -j ACCEPT
  sudo iptables -D FORWARD -i eth0 -o wlan0 -p tcp --sport 9910 -s 192.168.100.2 -j ACCEPT
  sudo netfilter-persistent save
  ```

### Different Network Configuration

If your network uses different IP ranges, adjust the rules accordingly:
- Replace `192.168.1.91` with your Pi's WiFi IP
- Replace `192.168.100.2` with your ATEM's IP
- Replace `wlan0` with your WiFi interface name (check with `ip addr`)
- Replace `eth0` with your Ethernet interface name

## Security Considerations

These rules only forward UDP port 9910. All other traffic remains isolated between the networks. This is safe for local network use.

## What This Doesn't Affect

- ✅ Pi Connect continues to work normally
- ✅ SSH access continues to work
- ✅ Filmbot application continues to work
- ✅ Internet access via WiFi continues to work
- ✅ Local ATEM control from the Pi (via PyATEMMax) continues to work

---

**Last Updated:** 2026-01-12

