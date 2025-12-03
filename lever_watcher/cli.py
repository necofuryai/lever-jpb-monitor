# lever_watcher/cli.py
import click
from pathlib import Path
from .client import LeverClient
from .differ import JobDiffer
from .notifier import SlackNotifier, DiscordNotifier

@click.group()
def cli():
    """Lever Job Watcher - Monitor job postings on Lever"""
    pass

@cli.command()
@click.argument("company_id")
@click.option("--pattern", "-p", default=None, help="Regex pattern to filter jobs")
@click.option("--query", "-q", default=None, help="Query string for Lever API (e.g. 'location=Tokyo&commitment=Full-time')")
@click.option("--slack-webhook", envvar="SLACK_WEBHOOK_URL")
@click.option("--discord-webhook", envvar="DISCORD_WEBHOOK_URL")
@click.option("--storage", default="~/.lever-watcher", help="State storage directory")
def watch(company_id, pattern, query, slack_webhook, discord_webhook, storage):
    """Check for new jobs and notify"""
    client = LeverClient(company_id, query=query)
    storage_path = Path(storage).expanduser()
    differ = JobDiffer(storage_path)

    # Fetch jobs
    if pattern:
        jobs = client.fetch_jobs_matching(pattern)
    else:
        jobs = client.fetch_all_jobs()

    # Diff
    new_jobs = differ.get_new_jobs(company_id, jobs)

    if not new_jobs:
        click.echo("No new jobs found.")
        return

    click.echo(f"Found {len(new_jobs)} new job(s)!")

    # Notify
    notifiers = []
    if slack_webhook:
        notifiers.append(SlackNotifier(slack_webhook))
    if discord_webhook:
        notifiers.append(DiscordNotifier(discord_webhook, storage_path))

    for notifier in notifiers:
        notifier.notify(new_jobs, company_id)

@cli.command()
@click.argument("company_id")
def list_jobs(company_id):
    """List all current jobs"""
    client = LeverClient(company_id)
    for job in client.fetch_all_jobs():
        click.echo(f"[{job.team or 'N/A'}] {job.title} - {job.location}")

if __name__ == "__main__":
    cli()