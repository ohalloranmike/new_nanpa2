import argparse

from app.config import Config
from app.ingest import refresh_database


def main():
    parser = argparse.ArgumentParser(description="Refresh NANPA/CNAC SQLite database")
    parser.add_argument("--force", action="store_true", help="Force download and rebuild")
    args = parser.parse_args()

    config = Config()
    db_path = refresh_database(config, force=args.force)
    print(f"Database refreshed: {db_path}")


if __name__ == "__main__":
    main()
