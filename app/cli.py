import argparse

from app.db import SessionLocal
from app.modules.saas.models import ApiKey, OrganisationAccount
from app.modules.saas.security import generate_api_key


def create_api_key(org_name: str) -> str:
    raw, key_hash = generate_api_key()
    with SessionLocal() as session, session.begin():
        org = OrganisationAccount(name=org_name)
        session.add(org)
        session.flush()
        session.add(ApiKey(org_id=org.id, key_hash=key_hash))
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-api-key", help="create an organisation and an API key for it")
    create.add_argument("org_name")
    args = parser.parse_args()

    if args.command == "create-api-key":
        print(create_api_key(args.org_name))


if __name__ == "__main__":
    main()
