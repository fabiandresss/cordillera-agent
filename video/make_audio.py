"""Genera la narración del video con voz neuronal (edge-tts) y los tiempos de cada palabra.

Salida: video/audio/sNN.mp3 + sNN.json (palabras con tiempo) + sNN.wav (44,1 kHz mono).
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
AUD = HERE / "audio"
AUD.mkdir(exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "es-CL-CatalinaNeural"
RATE = "+4%"

SCRIPT = [
    "Hola. Les presentamos el agente de despacho y rutas: un sistema de inteligencia artificial que ayuda a una "
    "empresa de transporte a organizar sus entregas cada día.",
    "En el reparto diario siempre hay imprevistos. Un camión se avería, un cliente importante pide urgencia, o una "
    "entrega falla. Reorganizar todo a mano toma tiempo, y los clientes se enteran tarde.",
    "Con este sistema, el despachador solo escribe lo que ocurrió, con palabras normales, en un panel web. "
    "Por ejemplo: a las once, el camión tres se averió.",
    "El agente entiende el mensaje, recuerda casos parecidos y decide qué hacer. Luego planifica las entregas y "
    "revisa que el plan sea posible: el peso de los camiones, los horarios y los turnos. Si algo no cuadra, lo "
    "corrige, o pide ayuda a un supervisor.",
    "En segundos, el camión averiado sale del plan y sus entregas pasan a otros camiones. Los clientes afectados "
    "reciben un aviso, y el panel muestra el razonamiento del agente, paso a paso.",
    "El sistema tiene dos memorias. La corta guarda lo que pasó hoy. La larga busca casos pasados por su "
    "significado: si escribes, se me rompió una rueda, encuentra averías anteriores.",
    "La inteligencia artificial interpreta los mensajes y redacta los avisos, pero las decisiones importantes las "
    "toman reglas claras y verificables. Así, si el modelo se equivoca, las reglas lo corrigen. El sistema tiene "
    "cincuenta y siete pruebas automáticas, y funciona solo con herramientas gratuitas.",
    "Un asistente confiable, probado y fácil de usar. Gracias por su atención.",
]


async def one(i, text):
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    audio, words = bytearray(), []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            words.append({"t": chunk["offset"] / 1e7, "d": chunk["duration"] / 1e7, "w": chunk["text"]})
    mp3 = AUD / f"s{i:02d}.mp3"
    mp3.write_bytes(bytes(audio))
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(mp3), "-ar", "44100", "-ac", "1",
                    str(AUD / f"s{i:02d}.wav")], check=True)
    # duración real a partir del wav
    import wave
    with wave.open(str(AUD / f"s{i:02d}.wav")) as w:
        dur = w.getnframes() / w.getframerate()
    (AUD / f"s{i:02d}.json").write_text(json.dumps({"text": text, "duration": dur, "words": words}, ensure_ascii=False), encoding="utf-8")
    print(f"escena {i}: {dur:5.1f} s · {len(words)} palabras")
    return dur


async def main():
    total = 0
    for i, t in enumerate(SCRIPT, 1):
        total += await one(i, t)
    print(f"Narración total: {total:.1f} s")


if __name__ == "__main__":
    asyncio.run(main())
