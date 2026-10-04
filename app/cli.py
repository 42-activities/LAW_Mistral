import argparse

from app.db import SessionLocal
from app.modules.saas.models import ApiKey, OrganisationAccount
from app.modules.saas.security import generate_api_key
from app.modules.seed.france_uae import seed


def create_api_key(org_name: str) -> str:
    raw, key_hash = generate_api_key()
    with SessionLocal() as session, session.begin():
        org = OrganisationAccount(name=org_name)
        session.add(org)
        session.flush()
        session.add(ApiKey(org_id=org.id, key_hash=key_hash))
    return raw


def seed_france_uae() -> None:
    session = SessionLocal()
    try:
        seed(session)
        session.commit()
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-api-key", help="create an organisation and an API key for it")
    create.add_argument("org_name")
    sub.add_parser("seed-france-uae", help="seed the verified France-UAE golden fixture")
    args = parser.parse_args()

    if args.command == "create-api-key":
        print(create_api_key(args.org_name))
    elif args.command == "seed-france-uae":
        seed_france_uae()
        print("seeded France-UAE fixture")


if __name__ == "__main__":
    main()
