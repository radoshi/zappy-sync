# zappy-sync

[Zappy](https://zapier.com/zappy) is a neat little utility for quick capturing screenshots, GIFs,
and videos.

Files are stored locally. If you have a Zapier Premium account, they are also hosted in Zapier.

`zappy-sync` is a little utility to sync your local files to your own cloud storage. This currently
only supports Google Cloud Storage, but can be extended.

# Installation

```
pipx install zappy-sync
```

# Configuration

## GCP

GCP configuration is quite intense and not for the faint hearted. You need to do the following:

1. Setup a service account. Go to IAM -> Service Accounts, set it up.
2. Setup a bucket where you want your files shared. Go to Storage -> Browser, create a bucket.
3. Change the `defacl` on this bucket to be public by default. You can do this via the `gsutil` CLI.
   `gsutil defacl set public-read gs://your-bucket-name`
4. Create a JSON key for your service account. Go to IAM -> Service Accounts, click on your service
   account, click on "Add Key", select JSON. Download this key and save it somewhere safe. Recommend
   `~/.zappy/gcp.json`.

## Settings

You can run the whole thing with command line options but having a settings file will make things
easier. Store the settings file in `~/.zappy/settings.toml`. Here's my settings file:

```toml
directory = "~/Pictures/Zappy/"

[storage]
provider = "gcp"  # for now, only gcp is supported

[gcp]
project = "my-project-name"
bucket = "zappy"
credentials = "~/.zappy/gcpkey.json"
```

## Usage

Pretty straight forward. Run `zappy-sync` and it will watch the directory you specified in the
settings file. Any new files will be uploaded to your cloud storage. Deletions are not synced.

```
Usage: zappy-sync [OPTIONS]

Options:
  --directory TEXT    Directory to watch.
  --bucket TEXT       GCP Storage Bucket.
  --project TEXT      GCP Project ID.
  --upload-missing    Upload missing files.
  --credentials TEXT  GCP Service account credentials.
  --provider TEXT     Storage provider. Only gcp for now.
  -n, --dry-run       Dry run.
  --help              Show this message and exit.
```
