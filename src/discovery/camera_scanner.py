"""RTSP 카메라 자동 탐지 모듈 — 로컬 네트워크 스캔"""

import asyncio
import ipaddress
import logging
import socket
from typing import Callable

logger = logging.getLogger(__name__)

RTSP_PORT = 554
ALTERNATIVE_PORTS = [554, 8554, 5540]
TIMEOUT_SEC = 1.5
MAX_WORKERS = 50

COMMON_RTSP_PATHS = [
    "/stream1",
    "/stream2",
    "/live",
    "/live/main",
    "/live/sub",
    "/h264",
    "/h264/ch1/main/av_stream",
    "/h264/ch1/sub/av_stream",
    "/cam1",
    "/cam2",
    "",
    "/",
    "/onvif1",
    "/avstream",
    "/media/video1",
    "/video1",
    "/video2",
    "/ch1/main",
    "/ch1/sub",
]

BRAND_SIGNATURES: list[tuple[str, str, list[str]]] = [
    ("hikvision", "/ISAPI/System/status", ["Hikvision"]),
    ("dahua", "/cgi-bin/status", ["Dahua"]),
    ("axis", "/axis-cgi/io/video.cgi", ["Axis"]),
    ("bosch", "/bosch/device", ["Bosch"]),
    ("samsung", "/cgi-bin/vision", ["Samsung"]),
    ("hanwha", "/stw-cgi/system.cgi", ["Hanwha"]),
]


def _get_local_subnet() -> str | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return ".".join(local_ip.split(".")[:3]) + ".0/24"
    except Exception:
        return "192.168.1.0/24"


async def _probe_ip(ip: str, port: int, progress_cb: Callable | None = None) -> str | None:
    for path in COMMON_RTSP_PATHS:
        rtsp_url = f"rtsp://{ip}:{port}{path}"
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=TIMEOUT_SEC,
            )
            writer.close()
            await writer.wait_closed()
            if progress_cb:
                progress_cb(ip, rtsp_url)
            return rtsp_url
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            continue
    return None


async def _scan_range(subnet: str, ports: list[int] | None = None,
                      progress_cb: Callable | None = None) -> list[dict]:
    if ports is None:
        ports = [RTSP_PORT]
    network = ipaddress.ip_network(subnet, strict=False)
    hosts = [str(h) for h in network.hostlist() if h != network.network_address and h != network.broadcast_address]

    sem = asyncio.Semaphore(MAX_WORKERS)

    async def _scan_host(ip: str) -> dict | None:
        async with sem:
            for port in ports:
                url = await _probe_ip(ip, port, progress_cb)
                if url:
                    return {"id": f"cam_{ip.replace('.', '_')}", "rtsp_url": url, "ip": ip, "port": port}
            return None

    tasks = [_scan_host(h) for h in hosts]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


def scan_network_for_cameras(subnet: str | None = None,
                              ports: list[int] | None = None,
                              progress_cb: Callable | None = None) -> list[dict]:
    if subnet is None:
        subnet = _get_local_subnet()
    if ports is None:
        ports = [RTSP_PORT] + ALTERNATIVE_PORTS[1:]

    logger.info(f"Scanning subnet {subnet} on ports {ports}...")
    results = asyncio.run(_scan_range(subnet, ports, progress_cb))
    logger.info(f"Scan complete. Found {len(results)} camera(s).")
    return results


def scan_progress_callback(ip: str, url: str):
    logger.debug(f"  Found: {url}")
