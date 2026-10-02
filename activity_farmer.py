#!/usr/bin/env python3
"""
GitHub Activity Farmer (24/7 Continuous Activity & Contribution Generator)
Supports:
  - 24/7 continuous commit farming with randomized intervals and jitter
  - Past backfill (filling contribution grid historically)
  - Realistic commit message generation
  - Configurable git author identity for proper GitHub attribution
  - Auto-commit & auto-push loop
"""

import os
import sys
import time
import random
import datetime
import argparse
import subprocess
import hashlib
from typing import Optional, List

ACTIVITY_LOG_FILE = "ACTIVITY_FEED.log"

TYPES = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore", "build", "ci"]
SCOPES = ["core", "engine", "parser", "net", "auth", "cache", "crypto", "renderer", "worker", "db", "api"]
MESSAGES = [
    "update activity telemetry buffer",
    "optimize worker loop iteration cycle",
    "recalculate internal cryptographic state seed",
    "synchronize event dispatcher queue",
    "refresh telemetry sequence counter",
    "refactor pipeline state machine transitions",
    "update cache eviction heuristics",
    "bump heartbeat timestamp token",
    "align memory arena chunk offsets",
    "rebalance scheduler thread pool tasks",
    "compact ledger ring buffer entries",
    "normalize network socket backoff timings",
    "prune stale connection telemetry",
    "recompute checksum signatures across feed",
    "adjust jitter delay distribution parameters"
]

def run_git(args: List[str], cwd: Optional[str] = None, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        check=True
    )

def generate_commit_message() -> str:
    ctype = random.choice(TYPES)
    cscope = random.choice(SCOPES)
    cmsg = random.choice(MESSAGES)
    return f"{ctype}({cscope}): {cmsg}"

def update_activity_feed(repo_path: str, custom_text: Optional[str] = None) -> str:
    feed_path = os.path.join(repo_path, ACTIVITY_LOG_FILE)
    now = datetime.datetime.now(datetime.timezone.utc)
    entropy = hashlib.sha256(f"{now.isoformat()}-{random.random()}".encode("utf-8")).hexdigest()[:16]
    line = f"[{now.strftime('%Y-%m-%d %H:%M:%S UTC')}] [TOKEN:{entropy}] {custom_text or 'Heartbeat tick'}\n"
    
    with open(feed_path, "a", encoding="utf-8") as f:
        f.write(line)
        
    return line.strip()

def commit_and_push(
    repo_path: str,
    message: str,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    commit_date: Optional[datetime.datetime] = None,
    push: bool = True,
    remote: str = "origin",
    branch: str = "main"
):
    run_git(["add", ACTIVITY_LOG_FILE], cwd=repo_path)
    
    git_env = {}
    if author_name:
        git_env["GIT_AUTHOR_NAME"] = author_name
        git_env["GIT_COMMITTER_NAME"] = author_name
    if author_email:
        git_env["GIT_AUTHOR_EMAIL"] = author_email
        git_env["GIT_COMMITTER_EMAIL"] = author_email
    if commit_date:
        date_str = commit_date.strftime("%Y-%m-%d %H:%M:%S")
        git_env["GIT_AUTHOR_DATE"] = date_str
        git_env["GIT_COMMITTER_DATE"] = date_str
        
    cmd = ["commit", "-m", message]
    run_git(cmd, cwd=repo_path, env=git_env)
    
    if push:
        run_git(["push", remote, branch], cwd=repo_path)

def mode_continuous(args):
    print(f"[*] Starting 24/7 Activity Farmer daemon...")
    print(f"[*] Repository: {args.repo}")
    print(f"[*] Author Name: {args.name or 'Git Default'}")
    print(f"[*] Author Email: {args.email or 'Git Default'}")
    print(f"[*] Interval: {args.interval_min}-{args.interval_max}s | Batch commits: {args.batch_min}-{args.batch_max}")
    print(f"[*] Auto-push: {not args.no_push}")
    
    cycle = 0
    total_commits = 0
    
    try:
        while True:
            cycle += 1
            batch_count = random.randint(args.batch_min, args.batch_max)
            print(f"\n[Cycle #{cycle}] Generating {batch_count} commit(s)...")
            
            for i in range(batch_count):
                msg = generate_commit_message()
                log_entry = update_activity_feed(args.repo, msg)
                commit_and_push(
                    repo_path=args.repo,
                    message=msg,
                    author_name=args.name,
                    author_email=args.email,
                    push=False
                )
                total_commits += 1
                print(f"  + [{total_commits}] {msg}")
                time.sleep(random.uniform(0.5, 2.0))
                
            if not args.no_push:
                print(f"[*] Pushing commits to {args.remote}/{args.branch}...")
                try:
                    run_git(["push", args.remote, args.branch], cwd=args.repo)
                    print(f"[+] Push successful.")
                except subprocess.CalledProcessError as e:
                    print(f"[-] Push failed: {e.stderr}", file=sys.stderr)
                    
            delay = random.randint(args.interval_min, args.interval_max)
            next_run = datetime.datetime.now() + datetime.timedelta(seconds=delay)
            print(f"[*] Sleeping for {delay} seconds (next trigger at {next_run.strftime('%H:%M:%S')})...")
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\n[*] Activity farmer stopped by user.")

def mode_backfill(args):
    print(f"[*] Starting Historical Contribution Grid Backfill...")
    print(f"[*] Days to backfill: {args.days}")
    print(f"[*] Daily commits range: {args.commits_min} - {args.commits_max}")
    
    today = datetime.datetime.now()
    total_commits = 0
    
    for day_offset in range(args.days, 0, -1):
        target_day = today - datetime.timedelta(days=day_offset)
        n_commits = random.randint(args.commits_min, args.commits_max)
        
        for _ in range(n_commits):
            hour = random.randint(8, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            commit_time = target_day.replace(hour=hour, minute=minute, second=second)
            
            msg = generate_commit_message()
            update_activity_feed(args.repo, f"Backfill {msg}")
            commit_and_push(
                repo_path=args.repo,
                message=msg,
                author_name=args.name,
                author_email=args.email,
                commit_date=commit_time,
                push=False
            )
            total_commits += 1
            
        print(f"[+] Day {target_day.strftime('%Y-%m-%d')}: {n_commits} commits generated.")
        
    if not args.no_push:
        print(f"[*] Pushing all {total_commits} backfilled commits to {args.remote}/{args.branch}...")
        run_git(["push", args.remote, args.branch], cwd=args.repo)
        print(f"[+] Backfill pushed successfully.")
        
    print(f"[+] Completed backfilling {total_commits} commits across {args.days} days.")

def main():
    parser = argparse.ArgumentParser(description="24/7 GitHub Activity & Contribution Matrix Farmer")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: current directory)")
    parser.add_argument("--name", default=None, help="Git author name")
    parser.add_argument("--email", default=None, help="Git author email linked to your GitHub profile")
    parser.add_argument("--remote", default="origin", help="Git remote name (default: origin)")
    parser.add_argument("--branch", default="main", help="Git branch name (default: main)")
    parser.add_argument("--no-push", action="store_true", help="Commit locally without pushing")
    
    subparsers = parser.add_subparsers(dest="mode", required=True)
    
    # Daemon continuous mode
    parser_daemon = subparsers.add_parser("daemon", help="Run 24/7 continuous activity farming loop")
    parser_daemon.add_argument("--interval-min", type=int, default=1800, help="Min delay between commit cycles in seconds (default: 1800 = 30 min)")
    parser_daemon.add_argument("--interval-max", type=int, default=7200, help="Max delay between commit cycles in seconds (default: 7200 = 2 hours)")
    parser_daemon.add_argument("--batch-min", type=int, default=1, help="Min commits per cycle (default: 1)")
    parser_daemon.add_argument("--batch-max", type=int, default=5, help="Max commits per cycle (default: 5)")
    
    # Backfill historical mode
    parser_backfill = subparsers.add_parser("backfill", help="Backfill historical commits to light up github grid")
    parser_backfill.add_argument("--days", type=int, default=30, help="Number of past days to populate (default: 30)")
    parser_backfill.add_argument("--commits-min", type=int, default=2, help="Min commits per day (default: 2)")
    parser_backfill.add_argument("--commits-max", type=int, default=8, help="Max commits per day (default: 8)")
    
    # Single test tick
    subparsers.add_parser("tick", help="Generate single immediate commit & push cycle")

    args = parser.parse_args()
    args.repo = os.path.abspath(args.repo)
    
    if args.mode == "daemon":
        mode_continuous(args)
    elif args.mode == "backfill":
        mode_backfill(args)
    elif args.mode == "tick":
        msg = generate_commit_message()
        print(f"[*] Executing immediate tick: {msg}")
        update_activity_feed(args.repo, msg)
        commit_and_push(
            repo_path=args.repo,
            message=msg,
            author_name=args.name,
            author_email=args.email,
            push=not args.no_push,
            remote=args.remote,
            branch=args.branch
        )
        print("[+] Tick complete.")

if __name__ == "__main__":
    main()
