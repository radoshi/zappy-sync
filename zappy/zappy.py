import os
import platform
from pathlib import Path

import click
import tomli
from google.cloud import storage
from rich.console import Console
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.fsevents import FSEventsObserver

console = Console()


def get_observer():
    if platform.system() == "Darwin":
        console.print("Using FSEventsObserver")
        return FSEventsObserver
    else:
        console.print("Using Observer")
        return Observer


def load_config():
    config_dir = Path.home() / ".zappy"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "settings.toml"

    if not config_path.exists():
        default_config = """
        [storage]
        provider = "gcp"

        [gcp]
        project = "your-gcp-project-id"
        bucket = "zappy"
        credentials = "gcpkey.json"
        """
        config_path.write_text(default_config.strip())

    with config_path.open("rb") as f:
        config = tomli.load(f)

    return config


class FsHandler(FileSystemEventHandler):
    def __init__(self, bucket_name, dry_run=False):
        self.bucket_name = bucket_name
        self.dry_run = dry_run

    def on_created(self, event):
        if not event.is_directory:
            client = storage.Client()
            bucket = client.get_bucket(self.bucket_name)

            file_path = event.src_path
            blob_name = os.path.basename(file_path)
            blob = bucket.blob(blob_name)

            if blob.exists():
                console.print(
                    f"{file_path} already exists in {self.bucket_name}.",
                    style="bold blue",
                )
            else:
                if self.dry_run:
                    console.print(
                        f"{file_path} will be uploaded to {self.bucket_name}.",
                        style="bold blue",
                    )
                else:
                    blob.upload_from_filename(file_path)
                    console.print(
                        f"{file_path} uploaded to {self.bucket_name}.",
                        style="bold blue",
                    )


@click.command()
@click.option("--directory", help="Directory to watch.")
@click.option("--bucket", help="GCP Storage Bucket.")
@click.option("--project", help="GCP Project ID.")
@click.option(
    "--upload-missing", is_flag=True, default=False, help="Upload missing files."
)
@click.option(
    "--credentials",
    help="GCP Service account credentials.",
)
@click.option("--provider", help="Storage provider. Only gcp for now.")
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Dry run.")
def main(directory, bucket, project, upload_missing, credentials, dry_run, provider):
    config = load_config()
    directory = directory or config["directory"]
    directory = Path(directory).expanduser().resolve()
    if not directory.exists():
        console.print(f"{directory} does not exist.", style="bold red")
        return

    provider = provider or config["storage"]["provider"]
    if provider != "gcp":
        console.print(f"{provider} is not supported.", style="bold red")
        return

    bucket = bucket or config["gcp"]["bucket"]
    project = project or config["gcp"]["project"]

    credentials = credentials or config["gcp"]["credentials"]
    credentials = Path(credentials).expanduser().resolve()
    if not credentials.exists():
        console.print(f"{credentials} does not exist.", style="bold red")
        return
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials)

    if upload_missing:
        client = storage.Client()
        bucket = client.get_bucket(bucket)
        for file_path in directory.iterdir():
            if file_path.is_file():
                blob_name = os.path.basename(file_path)
                blob = bucket.blob(blob_name)
                if not blob.exists():
                    if dry_run:
                        console.print(
                            f"{file_path} will be uploaded to {bucket}.",
                            style="bold blue",
                        )
                    else:
                        blob.upload_from_filename(file_path)
                        console.print(
                            f"{file_path} uploaded to {bucket}.", style="bold blue"
                        )

    console.print(
        f"Monitoring {directory} for new files to upload to {bucket}...",
        style="bold green",
    )

    event_handler = FsHandler(bucket, dry_run=dry_run)
    observer = get_observer()(timeout=5)
    observer.schedule(event_handler, path=directory, recursive=False)
    observer.start()

    console.print("Observer started. Press Ctrl+C to exit.", style="bold green")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
