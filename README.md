# Satisfactory File Mover

A simple Python tool that automatically monitors and moves Satisfactory game files (save files and blueprints) from a source directory to organized destination directories.

## Features

- Automatically detects and moves Satisfactory save files (`.sav` files ending with "CALCULATOR")
- Automatically detects and moves Satisfactory blueprint files (`.sbp` and `.sbpcfg`)
- Polls the source directory at configurable intervals
- Ensures files are stable (not being written to) before moving
- Prevents duplicate processing with file signature caching
- Supports cross-device moves (copy + remove fallback)

## Requirements

- Python 3.11+
- pytest (for testing)

## Environment Variables

- `SOURCE_PATH` - Source directory to monitor (required)
- `SAVE_PATH` - Destination directory for save files (required)
- `BLUEPRINT_PATH` - Destination directory for blueprint files (required)
- `POLL_INTERVAL` - Polling interval in seconds (default: 2.0)
- `FILE_STABILITY_DELAY` - Delay in seconds to wait for file stability (default: 1.0)

## Usage

### Running Locally

```bash
python mover/main.py
```

Make sure to set the required environment variables before running.

### Running with Docker

```bash
docker-compose up -d
```

Configure the volume paths in `docker-compose.yml` or set the environment variables:
- `SOURCE_VOLUME_PATH`
- `SAVES_VOLUME_PATH`
- `BLUEPRINTS_VOLUME_PATH`

## Testing

```bash
pytest mover/test_main.py
```

