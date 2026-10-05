import argparse
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.modules.saas import service
from app.modules.saas.models import ROLES, OrganisationAccount
from app.modules.seed.france_uae import seed


def _org(session: Session, name: str) -> OrganisationAccount:
    org = session.scalar(select(OrganisationAccount).where(OrganisationAccount.name == name))
    if org is None:
        org = OrganisationAccount(name=name)
        session.add(org)
        session.flush()
    return org


def create_api_key(org_name: str, role: str = "analyst", name: str = "cli") -> str:
    with SessionLocal() as session, session.begin():
        org = _org(session, org_name)
        raw, _ = service.create_api_key(
            session, org_id=org.id, name=name, role=role, actor_id=None
        )
    return raw


def create_user(org_name: str, email: str, name: str | None, role: str, password: str) -> None:
    with SessionLocal() as session, session.begin():
        org = _org(session, org_name)
        service.create_user(
            session, org_id=org.id, email=email, name=name, role=role, password=password,
            actor_id=None,
        )


def _read_password(from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\n")
    first = getpass.getpass("Password (min 12 characters): ")
    if first != getpass.getpass("Repeat password: "):
        sys.exit("passwords do not match")
    return first


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
    create = sub.add_parser(
        "create-api-key", help="create an API key for an organisation (created if missing)"
    )
    create.add_argument("org_name")
    create.add_argument("--role", choices=ROLES, default="analyst")
    create.add_argument("--name", default="cli")
    user = sub.add_parser("create-user", help="create a user (organisation created if missing)")
    user.add_argument("--org", required=True)
    user.add_argument("--email", required=True)
    user.add_argument("--name")
    user.add_argument("--role", choices=ROLES, default="admin")
    user.add_argument("--password-stdin", action="store_true")
    sub.add_parser("seed-france-uae", help="seed the verified France-UAE golden fixture")
    args = parser.parse_args()

    if args.command == "create-api-key":
        print(create_api_key(args.org_name, args.role, args.name))
    elif args.command == "create-user":
        try:
            create_user(
                args.org, args.email, args.name, args.role, _read_password(args.password_stdin)
            )
        except ValueError as exc:
            sys.exit(str(exc))
        print(f"created {args.role} {args.email} in {args.org}")
    elif args.command == "seed-france-uae":
        seed_france_uae()
        print("seeded France-UAE fixture")


if __name__ == "__main__":
    main()
