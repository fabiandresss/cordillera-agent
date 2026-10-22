"""Diseño de sonido sintetizado (sin archivos externos): efectos, música de fondo y mezcla final."""
import numpy as np
from scipy.signal import butter, lfilter

SR = 44100
RNG = np.random.default_rng(7)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


# ------------------------------------------------------------------ efectos
def whoosh(dur=0.75, f0=380, f1=3600):
    n = int(dur * SR)
    noise = RNG.standard_normal(n)
    out = np.zeros(n)
    chunks = 24
    size = n // chunks
    zi = None
    for k in range(chunks):
        lo = f0 + (f1 - f0) * (k / chunks) ** 1.6
        hi = min(lo * 1.9, SR / 2 - 100)
        b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], btype="band")
        seg = noise[k * size:(k + 1) * size] if k < chunks - 1 else noise[k * size:]
        y, _ = lfilter(b, a, seg, zi=np.zeros(max(len(a), len(b)) - 1))
        out[k * size:k * size + len(y)] = y
    t = _t(dur)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2.2
    return _norm(out * env, 0.9)


def click():
    t = _t(0.09)
    tone = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90)
    burst = RNG.standard_normal(len(t)) * np.exp(-t * 400) * 0.6
    return _norm(tone + burst, 0.8)


def tick():
    t = _t(0.03)
    return _norm(RNG.standard_normal(len(t)) * np.exp(-t * 250) + np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 200), 0.35)


def pop(f=620):
    t = _t(0.16)
    freq = f * (1 + 0.55 * (1 - np.exp(-t * 28)))
    ph = 2 * np.pi * np.cumsum(freq) / SR
    return _norm(np.sin(ph) * np.exp(-t * 22), 0.7)


def chime(base=880, dur=2.4):
    t = _t(dur)
    out = np.zeros(len(t))
    for mult, amp, dec in ((1, 1.0, 2.2), (2.76, 0.45, 3.2), (5.4, 0.2, 5.0), (0.5, 0.35, 1.6)):
        out += amp * np.sin(2 * np.pi * base * mult * t) * np.exp(-t * dec)
    out *= np.minimum(t / 0.004, 1)
    return _norm(out, 0.75)


def riser(dur=1.2):
    t = _t(dur)
    f = 300 + 900 * (t / dur) ** 2
    ph = 2 * np.pi * np.cumsum(f) / SR
    return _norm(np.sin(ph) * (t / dur) ** 1.5 * np.exp(-((t - dur) / 0.25) ** 2 * 0), 0.5)


def success():
    out = np.zeros(int(0.9 * SR))
    for i, f in enumerate((660, 880, 1320)):
        s = chime(f, 0.7)[: int(0.7 * SR)] * 0.7
        o = int(i * 0.09 * SR)
        out[o:o + len(s)] += s[: len(out) - o]
    return _norm(out, 0.7)


SFX = {"whoosh": whoosh, "click": click, "tick": tick, "pop": pop, "chime": chime, "riser": riser, "success": success}
_cache = {}


def sfx(name):
    if name not in _cache:
        _cache[name] = SFX[name]()
    return _cache[name]


# ------------------------------------------------------------------ música (pad ambiental + arpegio suave)
def _note(freq):
    return freq


def music(total):
    bpm = 82
    beat = 60 / bpm
    chords = [  # Am9 · Fmaj7 · Cmaj7 · G6 (frecuencias en Hz)
        ([110.0, 220.0, 261.63, 329.63, 392.0], [440.0, 523.25, 659.25, 783.99]),
        ([87.31, 174.61, 220.0, 261.63, 329.63], [349.23, 440.0, 523.25, 659.25]),
        ([130.81, 261.63, 329.63, 392.0, 493.88], [523.25, 659.25, 783.99, 987.77]),
        ([98.0, 196.0, 246.94, 293.66, 392.0], [392.0, 493.88, 587.33, 783.99]),
    ]
    n = int(total * SR)
    pad = np.zeros(n)
    arp = np.zeros(n)
    bar = 8 * beat
    k = 0
    while k * bar < total + bar:
        pad_f, arp_f = chords[k % 4]
        start = k * bar
        t = _t(bar + 2.2)
        env = np.minimum(t / 1.6, 1) * np.exp(-np.maximum(t - bar, 0) / 0.9)
        seg = np.zeros(len(t))
        for j, f in enumerate(pad_f):
            for det in (-0.9, 0.0, 0.9):
                seg += np.sin(2 * np.pi * (f * (1 + det / 1000)) * t + j) * (0.5 if j == 0 else 0.22)
            seg += np.sin(2 * np.pi * f * 2 * t) * 0.04
        seg *= env
        i0 = int(start * SR)
        m = min(len(seg), n - i0)
        if m > 0:
            pad[i0:i0 + m] += seg[:m]
        # arpegio: corcheas con patrón simple
        pattern = [0, 2, 1, 3, 2, 1, 3, 2, 0, 3, 1, 2, 3, 1, 2, 0]
        step = beat / 2
        for s_i, idx in enumerate(pattern):
            on = start + s_i * step
            if on >= total:
                break
            f = arp_f[idx % len(arp_f)] * (2 if s_i % 8 == 4 else 1)
            tt = _t(1.4)
            pl = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2 * tt)) * np.exp(-tt * 4.2)
            pl *= np.minimum(tt / 0.006, 1) * (0.55 + 0.45 * ((s_i % 4) == 0))
            i1 = int(on * SR)
            m = min(len(pl), n - i1)
            if m > 0:
                arp[i1:i1 + m] += pl[:m] * 0.5
        k += 1
    # eco para espacio
    d = int(beat * 0.75 * SR)
    wet = arp.copy()
    for rep, g in ((1, 0.38), (2, 0.2), (3, 0.1)):
        wet[d * rep:] += arp[: n - d * rep] * g
    b, a = butter(2, 2400 / (SR / 2), btype="low")
    pad = lfilter(b, a, pad)
    mix = pad * 0.55 + wet * 0.5
    fade_in = np.minimum(_t(total)[:n] / 2.0, 1)
    fade_out = np.minimum((total - _t(total)[:n]) / 3.0, 1)
    mix *= fade_in * np.clip(fade_out, 0, 1)
    return mix / (np.sqrt(np.mean(mix ** 2)) or 1.0)   # RMS = 1


# ------------------------------------------------------------------ mezcla
def place(buf, snd, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i < 0:
        snd = snd[-i:]
        i = 0
    m = min(len(snd), buf.shape[0] - i)
    if m <= 0:
        return
    gl = gain * (1 - max(pan, 0))
    gr = gain * (1 + min(pan, 0))
    buf[i:i + m, 0] += snd[:m] * gl
    buf[i:i + m, 1] += snd[:m] * gr


def mix_all(total, voices, events, music_rms=0.032, voice_rms=0.13):
    """voices: [(inicio_seg, array_mono)] ; events: [(tiempo, nombre, ganancia, pan)]"""
    n = int(total * SR)
    out = np.zeros((n, 2))
    voice_env = np.zeros(n)
    for start, v in voices:
        rms = np.sqrt(np.mean(v ** 2)) or 1.0
        v = v / rms * voice_rms
        place(out, v, start, 1.0)
        i = int(start * SR)
        m = min(len(v), n - i)
        voice_env[i:i + m] = 1.0
    # ducking suave de la música bajo la voz
    k = int(0.35 * SR)
    smooth = np.convolve(voice_env, np.ones(k) / k, mode="same")
    mus = music(total)[:n] * music_rms
    mus *= (1 - 0.5 * smooth)
    out[:, 0] += mus
    out[:, 1] += mus * 0.97
    for t, name, g, pan in events:
        place(out, sfx(name), t, g, pan)
    peak = np.max(np.abs(out))
    out = np.tanh(out * 1.15) / np.tanh(1.15)          # limitador suave
    out *= 0.89 / (np.max(np.abs(out)) or 1.0)
    return out.astype(np.float32)
