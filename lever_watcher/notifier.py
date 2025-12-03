# lever_watcher/notifier.py
from abc import ABC, abstractmethod
import httpx
import json
from pathlib import Path
from .client import LeverJob

class Notifier(ABC):
    @abstractmethod
    def notify(self, jobs: list[LeverJob], company_id: str) -> None:
        pass

class SlackNotifier(Notifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def notify(self, jobs: list[LeverJob], company_id: str) -> None:
        if not jobs:
            return
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {len(jobs)} new job(s) at {company_id}!"
                }
            }
        ]
        
        for job in jobs:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{job.apply_url}|{job.title}>*\n📍 {job.location} | 👥 {job.team or 'N/A'}"
                }
            })
        
        httpx.post(self.webhook_url, json={"blocks": blocks})

class DiscordNotifier(Notifier):
    def __init__(self, webhook_url: str, storage_path: Path = None):
        self.webhook_url = webhook_url
        self.storage_path = storage_path or Path.home() / ".lever-watcher"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_path / "discord_notified.json"
    
    def notify(self, jobs: list[LeverJob], company_id: str) -> None:
        if not jobs:
            return

        # Load notification history
        notified_ids = self._load_notification_history()

        # Filter out already notified jobs
        jobs_to_notify = [job for job in jobs if job.id not in notified_ids]

        if not jobs_to_notify:
            return

        embeds = [
            {
                "title": job.title,
                "url": job.apply_url,
                "fields": [
                    {"name": "Location", "value": job.location, "inline": True},
                    {"name": "Team", "value": job.team or "N/A", "inline": True},
                ],
                "color": 0x00ff00,
            }
            for job in jobs_to_notify
        ]

        # Discord limit: 10 embeds per message
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i+10]
            batch_start = i + 1
            batch_end = min(i + 10, len(jobs_to_notify))

            content = f"🚨 **{len(jobs_to_notify)} new job(s) at {company_id}!**"
            if len(embeds) > 10:
                content += f" ({batch_start}-{batch_end})"

            httpx.post(self.webhook_url, json={
                "content": content,
                "embeds": batch,
            })

        # Save notification history
        new_notified_ids = notified_ids | {job.id for job in jobs_to_notify}
        self._save_notification_history(new_notified_ids)

    def _load_notification_history(self) -> set[str]:
        """Load the set of job IDs that have already been notified"""
        if not self.history_file.exists():
            return set()
        try:
            data = json.loads(self.history_file.read_text())
            return set(data.get("notified_ids", []))
        except (json.JSONDecodeError, KeyError):
            return set()

    def _save_notification_history(self, notified_ids: set[str]) -> None:
        """Save the set of job IDs that have been notified"""
        self.history_file.write_text(
            json.dumps({"notified_ids": list(notified_ids)}, indent=2)
        )