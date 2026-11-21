
import os
import json
import base64
import logging
import asyncio
from dotenv import load_dotenv
import websockets

load_dotenv()

logger = logging.getLogger(__name__)

STT_URL = "wss://api.vachana.ai/stt/v3/stream"
TTS_URL = "wss://api.vachana.ai/api/v1/tts"

STT_MODEL = "prisma-v3.0"
TTS_MODEL = "timbre-v3.0"
TTS_VOICE = "Sunaina"

CONNECTION_TIMEOUT = 20
AUDIO_SAMPLE_RATE = 16000


def get_api_key():
    key = os.getenv("GNANI_API_KEY")

    if not key:
        raise RuntimeError(
            "GNANI_API_KEY is missing from your .env file."
        )

    return key


async def open_prisma_connection(language="hi"):
    api_key = get_api_key()

    # Updated: use exactly one locale
    language_code = (
        "en-IN" if language == "en"
        else "hi-IN"
    )

    headers = {
        "x-api-key-id": api_key,
        "model": STT_MODEL,
        "language_code": language_code,
        "x-sample-rate": str(AUDIO_SAMPLE_RATE),
        "format": "transcribe",
        "x-idle-timeout-sec": "300",
    }

    try:
        return await asyncio.wait_for(
            websockets.connect(
                STT_URL,
                additional_headers=headers,
                max_size=None,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5,
            ),
            timeout=CONNECTION_TIMEOUT,
        )

    except asyncio.TimeoutError as exc:
        logger.error("Gnani STT connection timed out")
        raise RuntimeError("Speech service connection timed out.") from exc

    except Exception:
        logger.exception("Gnani STT connection failed")
        raise


async def send_prisma_audio(connection, pcm_frame):
    if not isinstance(pcm_frame, bytes):
        raise TypeError("Audio frame must be bytes.")

    if len(pcm_frame) != 1024:
        raise ValueError(
            "Prisma audio frames must contain exactly 1024 bytes."
        )

    try:
        await connection.send(pcm_frame)

    except websockets.exceptions.ConnectionClosed as exc:
        logger.error("STT connection closed while sending audio")
        raise RuntimeError("Speech connection was interrupted.") from exc


async def commit_prisma_utterance(connection):
    try:
        await connection.send(json.dumps({"type": "commit"}))

    except websockets.exceptions.ConnectionClosed as exc:
        logger.error("STT connection closed before commit")
        raise RuntimeError("Could not finish speech recognition.") from exc


async def synthesize_speech(text, language="en"):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Speech text cannot be empty.")

    api_key = get_api_key()

    language_code = (
        "hi-IN" if language == "hi"
        else "en-IN"
    )

    headers = {
        "X-API-Key-ID": api_key,
    }

    request = {
        "text": text,
        "voice": TTS_VOICE,
        "model": TTS_MODEL,
        "language": language_code,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 24000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "raw",
        },
    }

    try:
        async with websockets.connect(
            TTS_URL,
            additional_headers=headers,
            max_size=None,
            open_timeout=CONNECTION_TIMEOUT,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=5,
        ) as connection:

            await connection.send(json.dumps(request))

            async for message in connection:
                try:
                    event = json.loads(message)
                except (json.JSONDecodeError, TypeError) as exc:
                    raise RuntimeError(
                        "Invalid response received from Gnani TTS."
                    ) from exc

                if event.get("type") == "error":
                    raise RuntimeError(
                        event.get("message", "Gnani TTS error")
                    )

                if event.get("type") == "audio":
                    audio_data = event.get("data", {}).get("audio")

                    if not audio_data:
                        logger.warning("Received empty TTS audio chunk")
                        continue

                    try:
                        audio_bytes = base64.b64decode(
                            audio_data,
                            validate=True,
                        )
                    except (ValueError, TypeError) as exc:
                        raise RuntimeError(
                            "Invalid audio data received from Gnani."
                        ) from exc

                    if audio_bytes:
                        yield audio_bytes

                if event.get("type") == "complete":
                    return

    except asyncio.TimeoutError as exc:
        logger.error("Gnani TTS connection timed out")
        raise RuntimeError("Voice response timed out.") from exc

    except websockets.exceptions.ConnectionClosed as exc:
        logger.error("Gnani TTS connection closed unexpectedly")
        raise RuntimeError("Voice response was interrupted.") from exc

    except RuntimeError:
        raise

    except Exception:
        logger.exception("Gnani TTS failed")
        raise
