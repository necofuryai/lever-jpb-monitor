# lever_watcher/notifier.py
from abc import ABC, abstractmethod
import httpx
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
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def notify(self, jobs: list[LeverJob], company_id: str) -> None:
        if not jobs:
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
            for job in jobs
        ]
        
        httpx.post(self.webhook_url, json={
            "content": f"🚨 **{len(jobs)} new job(s) at {company_id}!**",
            "embeds": embeds[:10],  # Discord limit
        })