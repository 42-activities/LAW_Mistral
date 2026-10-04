import sys

from app.db import SessionLocal
from app.modules.seed.france_uae import seed


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] != "seed-france-uae":
        print("usage: python -m app.cli seed-france-uae", file=sys.stderr)
        return 2
    session = SessionLocal()
    try:
        seed(session)
        session.commit()
    finally:
        session.close()
    print("seeded France-UAE fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
