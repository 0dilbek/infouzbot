import base64
import logging

import aiohttp

from config import IMGBB_API_KEY

_API = "https://api.imgbb.com/1/upload"


async def upload_image(image_bytes: bytes) -> str | None:
    """Upload image bytes to ImgBB, return public URL or None on failure."""
    if not IMGBB_API_KEY:
        logging.warning("IMGBB_API_KEY not set — skipping upload")
        return None
    encoded = base64.b64encode(image_bytes).decode()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                _API,
                data={"key": IMGBB_API_KEY, "image": encoded},
            ) as resp:
                result = await resp.json()
                return result["data"]["url"]
    except Exception as e:
        logging.error("ImgBB upload error: %s", e)
        return None
