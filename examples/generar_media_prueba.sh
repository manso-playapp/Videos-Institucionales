#!/usr/bin/env bash
# Genera media sintética para probar el pipeline sin material real:
#   bash examples/generar_media_prueba.sh && python3 tools/render_edl.py examples/edl-ejemplo.json --draft
set -euo pipefail
d="$(dirname "$0")/media"; mkdir -p "$d"; q=(-hide_banner -loglevel error -y)
ffmpeg "${q[@]}" -f lavfi -i testsrc2=s=3840x2160:r=50:d=8 -f lavfi -i "anoisesrc=d=8:c=pink:a=0.05" -c:v libx264 -preset ultrafast -c:a aac "$d/aereo_4k_50p.mp4"
ffmpeg "${q[@]}" -f lavfi -i "mandelbrot=s=1920x1080:r=25" -t 8 -c:v libx264 -preset ultrafast "$d/planta_1080_25p.mp4"
ffmpeg "${q[@]}" -f lavfi -i "smptehdbars=s=1920x1080:r=25" -t 6 -c:v libx264 -preset ultrafast "$d/detalle_1080_25p.mp4"
ffmpeg "${q[@]}" -f lavfi -i "aevalsrc='0.25*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*2*t))':d=40" "$d/musica.wav"
ffmpeg "${q[@]}" -f lavfi -i "aevalsrc='0.5*sin(2*PI*170*t)*gt(sin(2*PI*0.6*t),-0.2)':d=7" "$d/locucion.wav"
ffmpeg "${q[@]}" -f lavfi -i "anoisesrc=d=0.6:c=white:a=0.3" -af "afade=t=in:d=0.4,afade=t=out:st=0.4:d=0.2,highpass=f=800" "$d/whoosh.wav"
ffmpeg "${q[@]}" -f lavfi -i "color=c=0x1E6E6E:s=1200x360" -vf "drawtext=fontfile=assets/fonts/BarlowCondensed-Bold.ttf:text='MARCA':fontsize=220:fontcolor=white:x=(w-tw)/2:y=(h-th)/2" -frames:v 1 "$d/logo_placa.png"
ffmpeg "${q[@]}" -f lavfi -i "color=c=white@0.0:s=400x120,format=rgba" -vf "drawtext=fontfile=assets/fonts/BarlowCondensed-Bold.ttf:text='MARCA':fontsize=100:fontcolor=white:x=(w-tw)/2:y=(h-th)/2" -frames:v 1 "$d/logo_bug.png"
python3 tools/motion.py plantilla cierre -p '{"logo":"examples/media/logo_placa.png","frase":"Soluciones en aluminio desde 1979","web":"www.marca.com.ar","logo_ancho":620,"dur":4}' -o "$d/cierre.mov" >/dev/null
printf '1\n00:00:00,300 --> 00:00:02,800\nHace más de 45 años diseñamos\ny fabricamos soluciones en aluminio.\n\n2\n00:00:03,100 --> 00:00:06,200\nCalidad, compromiso y tecnología\nen cada proyecto.\n' > "$d/locucion.srt"
echo "Media de prueba en $d"
