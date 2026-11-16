#!/usr/bin/env python3
"""Mide temblor: movimiento global cuadro a cuadro (correlación de fase) y su componente de alta frecuencia.
uso: jitter.py video [in] [dur]   -> px de jitter RMS a 320 px de ancho (más bajo = más suave)"""
import subprocess, sys, numpy as np
def frames(path, tin, dur, w=320, h=180):
    cmd = ["ffmpeg","-v","error","-ss",str(tin),"-i",path,"-t",str(dur),"-vf",f"scale={w}:{h},format=gray","-f","rawvideo","-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw)//(w*h); return np.frombuffer(raw[:n*w*h],dtype=np.uint8).reshape(n,h,w).astype(np.float32)
def shift(a,b):
    wa = np.hanning(a.shape[0])[:,None]*np.hanning(a.shape[1])[None,:]
    A=np.fft.fft2((a-a.mean())*wa); B=np.fft.fft2((b-b.mean())*wa)
    R=A*np.conj(B); R/=np.abs(R)+1e-9; r=np.fft.ifft2(R).real
    y,x=np.unravel_index(np.argmax(r),r.shape)
    if y>r.shape[0]//2:y-=r.shape[0]
    if x>r.shape[1]//2:x-=r.shape[1]
    return x,y
def jitter(path, tin=0, dur=4):
    f=frames(path,tin,dur)
    if len(f)<8: return None
    d=np.array([shift(f[i],f[i+1]) for i in range(len(f)-1)],dtype=np.float64)
    pos=np.cumsum(d,axis=0)                     # trayectoria de cámara
    k=7; ker=np.ones(k)/k
    sm=np.stack([np.convolve(pos[:,i],ker,mode="same") for i in range(2)],axis=1)
    res=(pos-sm)[k:-k]                         # lo que queda = temblor
    acc=np.diff(d,axis=0)                       # aceleración cuadro a cuadro
    return float(np.sqrt((res**2).mean())), float(np.sqrt((acc**2).mean()))
if __name__=="__main__":
    p=sys.argv[1]; a=float(sys.argv[2]) if len(sys.argv)>2 else 0; d=float(sys.argv[3]) if len(sys.argv)>3 else 4
    print(jitter(p,a,d))
