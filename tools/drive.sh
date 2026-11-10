#!/usr/bin/env bash
# drive.sh — Acceso a Google Drive con rclone usando las variables de entorno del entorno cloud.
#
# Requiere: RCLONE_DRIVE_TOKEN (JSON del token OAuth). Opcionales:
#           RCLONE_CONFIG_DRIVE_CLIENT_ID / RCLONE_CONFIG_DRIVE_CLIENT_SECRET.
#
# Uso:
#   tools/drive.sh ls   <ID_o_URL_carpeta>               lista archivos (tamaño, fecha, nombre)
#   tools/drive.sh pull <ID_o_URL_carpeta> <destino>     descarga la carpeta completa
#   tools/drive.sh push <archivo_o_carpeta> <ID_o_URL>   sube entregables a una carpeta
#   tools/drive.sh link <ID_o_URL_carpeta> <archivo>     link compartible de un archivo subido
set -euo pipefail

command -v rclone >/dev/null || { echo "Falta rclone. Ejecutá: bash setup.sh" >&2; exit 1; }
[[ -n "${RCLONE_DRIVE_TOKEN:-}" ]] || { echo "Falta RCLONE_DRIVE_TOKEN en el entorno." >&2; exit 1; }

# Remote 'drive' configurado 100% por variables de entorno (no se escribe ningún secreto a disco).
export RCLONE_CONFIG_DRIVE_TYPE=drive
export RCLONE_CONFIG_DRIVE_SCOPE=drive
export RCLONE_CONFIG_DRIVE_TOKEN="$RCLONE_DRIVE_TOKEN"

folder_id() {  # acepta ID o URL de Drive
  local s="$1"
  if [[ "$s" =~ folders/([A-Za-z0-9_-]+) ]]; then echo "${BASH_REMATCH[1]}"
  elif [[ "$s" =~ id=([A-Za-z0-9_-]+) ]]; then echo "${BASH_REMATCH[1]}"
  else echo "$s"; fi
}

cmd="${1:-}"; shift || true
case "$cmd" in
  ls)   rclone lsl drive: --drive-root-folder-id "$(folder_id "$1")" ;;
  pull) mkdir -p "$2"; rclone copy drive: "$2" --drive-root-folder-id "$(folder_id "$1")" \
          --transfers 4 --progress --stats-one-line ;;
  push) dest="$(folder_id "$2")"
        if [[ -d "$1" ]]; then rclone copy "$1" drive: --drive-root-folder-id "$dest" --progress --stats-one-line
        else rclone copyto "$1" "drive:$(basename "$1")" --drive-root-folder-id "$dest" --progress --stats-one-line; fi ;;
  link) rclone link "drive:$2" --drive-root-folder-id "$(folder_id "$1")" ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac
