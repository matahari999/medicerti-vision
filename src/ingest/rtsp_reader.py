import threading
import queue
import time
import cv2
import logging
from src.config.settings import RTSP_RECONNECT_DELAYS, RTSP_MAX_RECONNECTS, FRAME_QUEUE_MAXSIZE

logger = logging.getLogger(__name__)


class RTSPStreamReader:
    def __init__(self, rtsp_url: str, name: str = "cam0"):
        self.rtsp_url = rtsp_url
        self.name = name
        self.frame_queue: queue.Queue = queue.Queue(maxsize=FRAME_QUEUE_MAXSIZE)
        self._stopped = False
        self._thread: threading.Thread | None = None
        self._reconnect_count = 0
        self._frame_skip_counter = 0
        self.fps = 0.0
        self.resolution = (0, 0)

    def start(self):
        self._thread = threading.Thread(target=self._read_loop, daemon=True, name=f"rtsp-{self.name}")
        self._thread.start()
        logger.info(f"[{self.name}] RTSP reader started: {self.rtsp_url}")
        return self

    def _read_loop(self):
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if cap.isOpened():
            self.fps = cap.get(cv2.CAP_PROP_FPS)
            self.resolution = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            logger.info(f"[{self.name}] Stream opened: {self.resolution} @ {self.fps:.1f}fps")
            self._reconnect_count = 0

        while not self._stopped:
            if not cap.isOpened():
                self._reconnect_count += 1
                if self._reconnect_count > RTSP_MAX_RECONNECTS:
                    logger.error(f"[{self.name}] Max reconnects reached. Giving up.")
                    break
                delay = RTSP_RECONNECT_DELAYS[min(self._reconnect_count - 1, len(RTSP_RECONNECT_DELAYS) - 1)]
                logger.warning(f"[{self.name}] Reconnecting in {delay}s (attempt {self._reconnect_count})")
                time.sleep(delay)
                cap.open(self.rtsp_url, cv2.CAP_DSHOW)
                continue

            ret, frame = cap.read()
            if not ret:
                logger.warning(f"[{self.name}] Frame read failed, reconnecting...")
                cap.release()
                cap = cv2.VideoCapture()
                continue

            self._reconnect_count = 0

            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass

            self.frame_queue.put(frame)

        cap.release()
        logger.info(f"[{self.name}] Reader stopped.")

    def read(self, timeout: float = 1.0) -> cv2.Mat | None:
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self):
        self._stopped = True
        if self._thread:
            self._thread.join(timeout=2.0)
