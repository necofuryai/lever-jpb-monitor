# lever_watcher/client.py
import httpx
from dataclasses import dataclass
from typing import Optional

@dataclass
class LeverJob:
    id: str
    title: str
    team: Optional[str]
    location: str
    commitment: Optional[str]  # Full-time, Part-time等
    description: str
    apply_url: str
    created_at: int  # Unix timestamp

class LeverClient:
    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, company_id: str, query: str | None = None):
        self.company_id = company_id
        self.query = query
        self._client = httpx.Client(timeout=30.0)

    def fetch_all_jobs(self) -> list[LeverJob]:
        """全求人を取得"""
        url = f"{self.BASE_URL}/{self.company_id}"
        if self.query:
            url = f"{url}?{self.query}"
        response = self._client.get(url)
        response.raise_for_status()
        
        return [
            LeverJob(
                id=job["id"],
                title=job["text"],
                team=job.get("categories", {}).get("team"),
                location=job.get("categories", {}).get("location", "Unknown"),
                commitment=job.get("categories", {}).get("commitment"),
                description=job.get("descriptionPlain", ""),
                apply_url=job["applyUrl"].rstrip("/apply"),
                created_at=job["createdAt"],
            )
            for job in response.json()
        ]
    
    def fetch_jobs_matching(self, pattern: str) -> list[LeverJob]:
        """正規表現でフィルタリング"""
        import re
        regex = re.compile(pattern, re.IGNORECASE)
        all_jobs = self.fetch_all_jobs()
        
        return [
            job for job in all_jobs
            if regex.search(job.title) or regex.search(job.description)
        ]