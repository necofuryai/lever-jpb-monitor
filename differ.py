# lever_watcher/differ.py
import json
from pathlib import Path
from dataclasses import asdict

class JobDiffer:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_state_file(self, company_id: str) -> Path:
        return self.storage_path / f"{company_id}.json"
    
    def get_new_jobs(
        self, 
        company_id: str, 
        current_jobs: list[LeverJob]
    ) -> list[LeverJob]:
        """前回との差分を検出"""
        state_file = self._get_state_file(company_id)
        
        if not state_file.exists():
            # 初回は全件を保存して空リストを返す（初回で全件通知は鬱陶しい）
            self._save_state(state_file, current_jobs)
            return []
        
        previous_ids = set(json.loads(state_file.read_text()).keys())
        current_map = {job.id: job for job in current_jobs}
        
        new_jobs = [
            job for job_id, job in current_map.items()
            if job_id not in previous_ids
        ]
        
        self._save_state(state_file, current_jobs)
        return new_jobs
    
    def _save_state(self, path: Path, jobs: list[LeverJob]):
        state = {job.id: asdict(job) for job in jobs}
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2))