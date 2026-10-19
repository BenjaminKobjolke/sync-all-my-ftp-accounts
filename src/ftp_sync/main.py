"""CLI entry point and the central error handler."""

import argparse
import sys

from ftp_sync.app_logger import AppLogger
from ftp_sync.backup import BackupCoordinator
from ftp_sync.config.settings import Settings
from ftp_sync.models import AppKind
from ftp_sync.stores.registry import build_stores
from ftp_sync.sync_runner import SyncRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync stored FTP accounts between apps")
    parser.add_argument("--source", choices=[k.value for k in AppKind], help="app to sync from")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    AppLogger.configure(settings.log_level)
    AppLogger.info("Close FileZilla and Notepad++ first - they overwrite their config on exit.")
    try:
        stores = build_stores(settings, BackupCoordinator(settings.backup_dir))
        SyncRunner(stores).run(AppKind(args.source) if args.source else None)
    except KeyboardInterrupt:
        return 1
    except Exception as error:  # noqa: BLE001 - central handler: report, never traceback-dump
        AppLogger.error(str(error))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
