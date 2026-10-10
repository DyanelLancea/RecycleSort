"""Concurrent authenticated upload test for an already-running RecycleSort API."""

import asyncio
import math
import sys
import time
import uuid
from pathlib import Path

import httpx


async def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: python tests/load_test.py <base-url> <image-path> <seconds> <workers>"
        )
    base_url, image_path, seconds_text, workers_text = sys.argv[1:]
    seconds, workers = int(seconds_text), int(workers_text)
    if seconds <= 0 or workers <= 0:
        raise SystemExit("seconds and workers must both be positive integers")

    image_data = Path(image_path).read_bytes()
    async with httpx.AsyncClient(base_url=base_url, timeout=60) as client:
        email = f"load-{uuid.uuid4().hex[:8]}@example.com"
        registration = await client.post(
            "/api/auth/register",
            json={"email": email, "password": "LoadTest2026x"},
        )
        registration.raise_for_status()
        token = registration.json().get("access_token")
        if not token:
            raise RuntimeError("Registration response did not contain an access token")
        headers = {"Authorization": f"Bearer {token}"}

        end_time = time.time() + seconds
        response_times: list[float] = []
        status_codes: dict[int | str, int] = {}

        async def worker() -> None:
            while time.time() < end_time:
                started = time.perf_counter()
                try:
                    response = await client.post(
                        "/api/upload",
                        headers=headers,
                        files={"file": ("item.jpg", image_data, "image/jpeg")},
                    )
                    status_codes[response.status_code] = (
                        status_codes.get(response.status_code, 0) + 1
                    )
                except httpx.HTTPError:
                    status_codes["error"] = status_codes.get("error", 0) + 1
                response_times.append(time.perf_counter() - started)

        await asyncio.gather(*(worker() for _ in range(workers)))

    response_times.sort()
    if response_times:
        p50 = response_times[math.ceil(len(response_times) * 0.50) - 1]
        p95 = response_times[math.ceil(len(response_times) * 0.95) - 1]
    else:
        p50 = p95 = 0.0
    print(
        {
            "requests": len(response_times),
            "status_codes": status_codes,
            "p50_seconds": round(p50, 3),
            "p95_seconds": round(p95, 3),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
