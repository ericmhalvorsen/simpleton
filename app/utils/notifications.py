"""Notification service for alerts and system events"""

import logging
from datetime import datetime
from typing import Literal

import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via ntfy or Telegram"""

    def __init__(
        self,
        ntfy_url: str | None = None,
        ntfy_topic: str | None = None,
        telegram_bot_token: str | None = None,
        telegram_chat_id: str | None = None,
        enabled: bool = True,
    ):
        """
        Initialize notification service

        Args:
            ntfy_url: ntfy server URL (e.g., http://ntfy:80 or http://localhost:8080)
            ntfy_topic: ntfy topic name
            telegram_bot_token: Telegram bot token (optional)
            telegram_chat_id: Telegram chat ID (optional)
            enabled: Whether notifications are enabled
        """
        self.ntfy_url = ntfy_url
        self.ntfy_topic = ntfy_topic
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.enabled = enabled

        # Validate configuration
        self.ntfy_enabled = bool(ntfy_url and ntfy_topic and enabled)
        self.telegram_enabled = bool(telegram_bot_token and telegram_chat_id and enabled)

        if not enabled:
            logger.info("Notifications are disabled")
        elif self.ntfy_enabled:
            logger.info(f"Notifications enabled via ntfy: {ntfy_url}/{ntfy_topic}")
        elif self.telegram_enabled:
            logger.info("Notifications enabled via Telegram")
        else:
            logger.warning("Notifications enabled but no valid configuration found")

    async def send(
        self,
        title: str,
        message: str,
        priority: Literal["min", "low", "default", "high", "urgent"] = "default",
        tags: list[str] | None = None,
    ) -> bool:
        """
        Send notification via configured channels

        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (min, low, default, high, urgent)
            tags: Optional tags for categorization (e.g., ["warning", "alert"])

        Returns:
            True if at least one notification was sent successfully
        """
        if not self.enabled:
            logger.debug(f"Notification skipped (disabled): {title}")
            return False

        success = False

        # Send via ntfy
        if self.ntfy_enabled:
            try:
                success = await self._send_ntfy(title, message, priority, tags or [])
            except Exception as e:
                logger.error(f"Failed to send ntfy notification: {e}")

        # Send via Telegram
        if self.telegram_enabled:
            try:
                telegram_success = await self._send_telegram(title, message)
                success = success or telegram_success
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {e}")

        return success

    async def _send_ntfy(
        self,
        title: str,
        message: str,
        priority: str,
        tags: list[str],
    ) -> bool:
        """Send notification via ntfy"""
        try:
            url = f"{self.ntfy_url}/{self.ntfy_topic}"

            headers = {
                "Title": title,
                "Priority": priority,
                "Tags": ",".join(tags) if tags else "",
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, content=message, headers=headers)
                response.raise_for_status()

            logger.info(f"Sent ntfy notification: {title}")
            return True

        except Exception as e:
            logger.error(f"ntfy notification failed: {e}")
            return False

    async def _send_telegram(self, title: str, message: str) -> bool:
        """Send notification via Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"

            text = f"<b>{title}</b>\n\n{message}"

            payload = {
                "chat_id": self.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            logger.info(f"Sent Telegram notification: {title}")
            return True

        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False

    async def send_startup(self, service_name: str = "Simpleton", host: str = "localhost", port: int = 8000):
        """Send startup notification"""
        await self.send(
            title=f"🚀 {service_name} Started",
            message=f"Service is now running at http://{host}:{port}\nStarted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            priority="default",
            tags=["rocket", "startup"],
        )

    async def send_shutdown(self, service_name: str = "Simpleton"):
        """Send shutdown notification"""
        await self.send(
            title=f"🛑 {service_name} Shutdown",
            message=f"Service has stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            priority="low",
            tags=["stop", "shutdown"],
        )

    async def send_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Send alert notification"""
        priority_map = {
            "info": "low",
            "warning": "high",
            "error": "urgent",
            "critical": "urgent",
        }

        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🔥",
            "critical": "🚨",
        }

        await self.send(
            title=f"{emoji_map.get(severity, '⚠️')} Alert: {alert_type}",
            message=message,
            priority=priority_map.get(severity, "high"),
            tags=[severity, "alert"],
        )

    async def send_request_notification(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
    ):
        """Send notification for API request (useful for tracking usage)"""
        await self.send(
            title=f"🔔 API Request: {method} {path}",
            message=f"Status: {status_code}\nDuration: {duration:.3f}s\nTime: {datetime.now().strftime('%H:%M:%S')}",
            priority="min",  # Low priority for request notifications
            tags=["api", "request"],
        )


# Global notification service instance
_notification_service: NotificationService | None = None


def get_notification_service(
    ntfy_url: str | None = None,
    ntfy_topic: str | None = None,
    telegram_bot_token: str | None = None,
    telegram_chat_id: str | None = None,
    enabled: bool = True,
) -> NotificationService:
    """Get or create notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(
            ntfy_url=ntfy_url,
            ntfy_topic=ntfy_topic,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            enabled=enabled,
        )
    return _notification_service
