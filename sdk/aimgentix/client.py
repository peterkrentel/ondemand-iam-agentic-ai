"""
AIMgentix Client - Non-blocking audit event capture with buffering and retry
"""
import requests
import logging
import time
from typing import Optional, List
from queue import Queue
from threading import Thread, Event
from .events import AuditEvent

logger = logging.getLogger(__name__)


class AuditClient:
    """
    Non-blocking audit client with buffering and retry logic
    
    Features:
    - Async event capture (doesn't block agent execution)
    - Automatic buffering
    - Retry with exponential backoff
    - Graceful degradation (logs errors but doesn't crash)
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        buffer_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0
    ):
        """
        Initialize the audit client

        Args:
            api_url: Base URL of the AIMgentix API
            buffer_size: Maximum number of events to buffer before forcing flush
            flush_interval: Seconds between automatic flushes
            max_retries: Maximum retry attempts for failed requests
            retry_backoff: Initial backoff time in seconds (doubles each retry)
        """
        self.api_url = api_url.rstrip('/')
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        
        self._buffer: Queue = Queue(maxsize=buffer_size)
        self._stop_event = Event()
        self._flush_thread: Optional[Thread] = None
        
        # Start background flush thread
        self._start_flush_thread()
        
        logger.info(f"AuditClient initialized with API URL: {self.api_url}")
    
    def _start_flush_thread(self):
        """Start the background thread that flushes events"""
        self._flush_thread = Thread(target=self._flush_worker, daemon=True)
        self._flush_thread.start()
    
    def _flush_worker(self):
        """Background worker that periodically flushes buffered events"""
        while not self._stop_event.is_set():
            time.sleep(self.flush_interval)
            self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush all buffered events to the API"""
        events_to_send: List[AuditEvent] = []
        
        # Drain the queue
        while not self._buffer.empty():
            try:
                event = self._buffer.get_nowait()
                events_to_send.append(event)
            except Exception:
                break
        
        # Send events
        for event in events_to_send:
            self._send_event_with_retry(event)
    
    def _send_event_with_retry(self, event: AuditEvent):
        """Send a single event with retry logic"""
        backoff = self.retry_backoff
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.api_url}/v1/events",
                    json=event.to_dict(),
                    timeout=5.0
                )
                response.raise_for_status()
                logger.debug(f"Event {event.event_id} sent successfully")
                return
            
            except Exception as e:
                logger.warning(f"Failed to send event (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to send event {event.event_id} after {self.max_retries} attempts")
    
    def capture(self, event: AuditEvent):
        """
        Capture an audit event (non-blocking)
        
        Args:
            event: AuditEvent to capture
        """
        try:
            # Try to add to buffer
            if self._buffer.full():
                logger.warning("Buffer full, forcing flush")
                self._flush_buffer()
            
            self._buffer.put_nowait(event)
            logger.debug(f"Event {event.event_id} buffered")
        
        except Exception as e:
            logger.error(f"Failed to buffer event: {e}")
    
    def flush(self):
        """Manually flush all buffered events"""
        self._flush_buffer()
    
    def close(self):
        """Close the client and flush remaining events"""
        logger.info("Closing AuditClient...")
        self._stop_event.set()
        self._flush_buffer()
        
        if self._flush_thread:
            self._flush_thread.join(timeout=10.0)
        
        logger.info("AuditClient closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

