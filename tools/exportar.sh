#!/usr/bin/env bash
# exportar.sh — Genera el paquete de entrega a partir del master aprobado.
#
#   tools/exportar.sh render/master.mp4 entregas/Cliente_Institucional_2026
#
# Produce (nombres = <prefijo>_<variante>):
#   _Master_1080p.mp4   H.264 High ~20 Mbps (copia del master)
#   _ProRes422HQ.mov    mezzanine para TV / eventos / archivo
#   _Web_1080p.mp4      liviano (~8 Mbps) para web, LinkedIn, mail
#   _Poster.jpg         cuadro representativo (al 20% o --poster SEG)
#   _Contacto.jpg       hoja de contacto para revisión
set -euo pipefail
src="$1"; pre="$2"; poster="${3:-}"
mkdir -p "$(dirname "$pre")"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$src")
[[ -n "$poster" ]] || poster=$(python3 -c "print(round($dur*0.2,2))")
COLOR=(-colorspace bt709 -color_primaries bt709 -color_trc bt709)

cp "$src" "${pre}_Master_1080p.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$src" -c:v prores_ks -profile:v 3 -vendor apl0 \
  -pix_fmt yuv422p10le "${COLOR[@]}" -c:a pcm_s24le "${pre}_ProRes422HQ.mov"
ffmpeg -hide_banner -loglevel error -y -i "$src" -c:v libx264 -preset slow -b:v 8M -maxrate 10M \
  -bufsize 16M -pix_fmt yuv420p "${COLOR[@]}" -c:a aac -b:a 192k -movflags +faststart "${pre}_Web_1080p.mp4"
ffmpeg -hide_banner -loglevel error -y -ss "$poster" -i "$src" -frames:v 1 -q:v 2 "${pre}_Poster.jpg"
ffmpeg -hide_banner -loglevel error -y -i "$src" -vf "fps=24/$dur,scale=480:-2,tile=4x6:padding=4" \
  -frames:v 1 -q:v 3 "${pre}_Contacto.jpg"
ls -lh "${pre}"_*
