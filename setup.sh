#!/usr/bin/env bash
# setup.sh — Prepara una sesión nueva (nube o local) para editar. Idempotente.
set -euo pipefail
cd "$(dirname "$0")"
ok(){ printf '  ✅ %s\n' "$*"; }; warn(){ printf '  ⚠️  %s\n' "$*"; }

echo "Dependencias:"
command -v ffmpeg >/dev/null && ok "$(ffmpeg -version | head -1 | cut -d' ' -f1-3)" || { warn "falta ffmpeg → apt-get install -y ffmpeg"; }
if ! command -v rclone >/dev/null; then
  tmp=$(mktemp -d); curl -sSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o "$tmp/r.zip"
  unzip -oq "$tmp/r.zip" -d "$tmp" && install -m 755 "$tmp"/rclone-*-linux-amd64/rclone /usr/local/bin/rclone; rm -rf "$tmp"
fi
ok "$(rclone version | head -1)"
python3 -c "import faster_whisper" 2>/dev/null || pip install -q faster-whisper 2>&1 | grep -v WARNING || true
python3 -c "import faster_whisper" && ok "faster-whisper (transcripción local)" || warn "faster-whisper no disponible"
python3 -c "import numpy" && ok "numpy"

echo "Fuentes:"
ls assets/fonts/Inter-*.ttf >/dev/null && ok "Inter (assets/fonts)"
ls assets/fonts/BarlowCondensed-*.ttf >/dev/null && ok "Barlow Condensed (assets/fonts)"

echo "Google Drive:"
if [[ -n "${RCLONE_DRIVE_TOKEN:-}" ]]; then
  tools/drive.sh ls 1KXB3dRwdVJe9fg8ieclaclFpCV4sl7Q2 >/dev/null 2>&1 && ok "acceso OK (carpeta de referencias)" || warn "token presente pero sin acceso"
else warn "falta RCLONE_DRIVE_TOKEN en el entorno"; fi
