# 🎬 Media Stack

A self-hosted media server stack built with Docker Compose.

## Services

| Service | Port | Path | Purpose |
|---|---|---|---|
| **Jellyfin** | 8096 | `/` | Media server |
| **Sonarr** | 8989 | `/sonarr` | TV show management |
| **Radarr** | 7878 | `/radarr` | Movie management |
| **Prowlarr** | 9696 | `/prowlarr` | Indexer management |
| **qBittorrent** | 8080 | `/qbit` | Torrent client |
| **Seerr** | 5055 | `/seerr` | Media request UI |
| **FlareSolverr** | — | — | Cloudflare bypass |
| **Caddy** | 80 | — | Reverse proxy / router |
| **Cloudflared** | — | — | Cloudflare tunnel (remote access) |
| **Tailscale** | — | — | VPN mesh (LAN access) |
| **Dashboard** | — | `/` fallback | Custom service dashboard |

## Directory Structure

```
media/
├── docker-compose.yml          # Main stack definition
├── .env                        # Secrets (gitignored — copy from .env.example)
├── .env.example                # ← Template: copy to .env and fill in
│
├── config/
│   ├── caddy/
│   │   └── Caddyfile           # Reverse proxy routes (committed)
│   ├── prowlarr/
│   │   └── config.xml.template # ← Copy to config.xml on fresh install
│   ├── radarr/
│   │   └── config.xml.template
│   ├── sonarr/
│   │   └── config.xml.template
│   ├── seerr/
│   │   └── settings.json.template
│   ├── qbittorrent/
│   │   └── qBittorrent/
│   │       └── qBittorrent.conf.template
│   ├── jellyfin/               # Auto-generated on first run
│   ├── bazarr/                 # Auto-generated on first run
│   └── tailscale/              # Machine-specific, gitignored
│
├── data/
│   ├── library/
│   │   ├── movies/             # Radarr download target
│   │   ├── tv/                 # Sonarr download target
│   │   └── music/
│   └── downloads/
│       ├── complete/           # qBittorrent saves here
│       └── incomplete/
│
├── dashboard/                  # Custom Python dashboard (committed)
│   ├── Dockerfile
│   ├── server.py
│   └── static/
│
└── scripts/
    └── tailscale-start.sh.template   # Copy to config/tailscale/start.sh
```

## Fresh Machine Setup

### 1. Prerequisites

```bash
# Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Add user to video/render groups for Jellyfin HW transcoding
sudo usermod -aG video,render $USER
```

### 2. Clone & configure

```bash
git clone <your-repo-url> ~/services/media
cd ~/services/media
```

**Copy and fill in secrets:**
```bash
cp .env.example .env
nano .env  # paste your real CLOUDFLARE_TUNNEL_TOKEN
```

### 3. Bootstrap service configs

Each *arr app auto-generates its own `config.xml` and API key on first boot.
You only need the templates if you want to pre-set `UrlBase` before first run:

```bash
# Optional — pre-seed configs so UrlBase routing works immediately
cp config/prowlarr/config.xml.template config/prowlarr/config.xml
cp config/radarr/config.xml.template   config/radarr/config.xml
cp config/sonarr/config.xml.template   config/sonarr/config.xml
```

**Seerr** — copy template, then fill in API keys *after* the arr apps start:
```bash
cp config/seerr/settings.json.template config/seerr/settings.json
# Start the stack, grab API keys from each service UI, then update settings.json
```

**qBittorrent** — optional pre-seed:
```bash
cp config/qbittorrent/qBittorrent/qBittorrent.conf.template \
   config/qbittorrent/qBittorrent/qBittorrent.conf
```

### 4. Tailscale setup

```bash
# Copy and make the startup script executable
sudo cp scripts/tailscale-start.sh.template config/tailscale/start.sh
sudo chmod +x config/tailscale/start.sh

# Get a one-time auth key from https://login.tailscale.com/admin/settings/keys
# Then add to docker-compose.yml under tailscale environment:
#   TS_AUTHKEY: tskey-auth-xxxxx
```

### 5. Hardware transcoding (Intel iGPU)

The compose file assumes `/dev/dri/renderD128` and `/dev/dri/card1`.
Verify your GPU paths:
```bash
ls -la /dev/dri/
# Update docker-compose.yml devices section if paths differ

# Get video group GID (the "44" in group_add)
getent group video | cut -d: -f3

# Get render group GID (the "993" in group_add)  
getent group render | cut -d: -f3
```

### 6. Start the stack

```bash
docker compose up -d
```

### 7. Post-start configuration

After all containers are healthy:

1. **Jellyfin** (`http://localhost:8096`) — Complete setup wizard, add libraries:
   - Movies → `/media/movies`
   - TV → `/media/tv`

2. **Prowlarr** (`/prowlarr`) — Add indexers, then sync to Sonarr/Radarr

3. **Radarr** (`/radarr`) — Set root folder to `/data/library/movies`, add download client (qBittorrent at `qbittorrent:8080`)

4. **Sonarr** (`/sonarr`) — Set root folder to `/data/library/tv`, add download client

5. **Seerr** (`/seerr`) — Connect to Jellyfin → grab API key from Jellyfin Admin → Update `config/seerr/settings.json` with real keys for Jellyfin, Radarr, Sonarr

6. **Cloudflare Tunnel** — Verify tunnel is active at [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com)

## API Keys Reference

After setup, note your API keys here (keep this file gitignored if you add real values):

| Service | Where to find the key |
|---|---|
| Jellyfin | Admin → API Keys |
| Radarr | Settings → General → API Key |
| Sonarr | Settings → General → API Key |
| Prowlarr | Settings → General → API Key |

## Updating

```bash
docker compose pull
docker compose up -d
```

## Backup

What to back up (everything NOT gitignored):
- `config/prowlarr/prowlarr.db` — indexer config & history
- `config/radarr/radarr.db` — movie library & history  
- `config/sonarr/sonarr.db` — TV library & history
- `config/seerr/db/db.sqlite3` — request history & users
- `config/jellyfin/config/` — Jellyfin metadata & users
- `config/qbittorrent/` — torrent state
