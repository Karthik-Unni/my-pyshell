"""Background job tracking."""
from __future__ import annotations

import os
import signal
from dataclasses import dataclass, field


@dataclass
class Job:
    job_id: int
    pgid: int
    pids: list[int]
    command: str
    status: str = "Running"  # Running, Stopped, Done


class JobTable:
    def __init__(self):
        self._jobs: dict[int, Job] = {}
        self._next_id = 1

    def add(self, pgid: int, pids: list[int], command: str) -> Job:
        job = Job(job_id=self._next_id, pgid=pgid, pids=pids, command=command)
        self._jobs[job.job_id] = job
        self._next_id += 1
        return job

    def get(self, job_id: int) -> Job | None:
        return self._jobs.get(job_id)

    def latest(self) -> Job | None:
        running = [j for j in self._jobs.values() if j.status != "Done"]
        return running[-1] if running else None

    def all_sorted(self) -> list[Job]:
        return sorted(self._jobs.values(), key=lambda j: j.job_id)

    def remove(self, job_id: int) -> None:
        self._jobs.pop(job_id, None)

    def reap_finished(self) -> list[Job]:
        """Non-blocking check for finished background jobs. Returns newly-done jobs."""
        finished = []
        for job in list(self._jobs.values()):
            if job.status == "Done":
                continue
            all_done = True
            for pid in job.pids:
                try:
                    wpid, _ = os.waitpid(pid, os.WNOHANG)
                    if wpid == 0:
                        all_done = False
                except ChildProcessError:
                    pass  # already reaped
            if all_done:
                job.status = "Done"
                finished.append(job)
        return finished

    def format_line(self, job: Job, latest_id: int | None = None) -> str:
        marker = "+" if job.job_id == latest_id else " "
        return f"[{job.job_id}]{marker}  {job.status:<10} {job.command}"

    def continue_job(self, job: Job, foreground: bool) -> None:
        job.status = "Running"
        try:
            os.killpg(job.pgid, signal.SIGCONT)
        except ProcessLookupError:
            job.status = "Done"
            return
        if foreground:
            for pid in job.pids:
                try:
                    os.waitpid(pid, 0)
                except ChildProcessError:
                    pass
            job.status = "Done"
