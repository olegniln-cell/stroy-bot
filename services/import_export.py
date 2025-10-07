# services/import_export.py
import csv
import sqlalchemy as sa
from models import User


async def export_users(session, filepath: str):
    users = await session.execute(sa.select(User))
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "tg_id", "email", "phone_number", "role", "created_at", "updated_at"]
        )
        for u in users.scalars():
            writer.writerow(
                [
                    u.id,
                    u.tg_id,
                    u.email,
                    u.phone_number,
                    u.role,
                    u.created_at,
                    u.updated_at,
                ]
            )


async def import_users(session, filepath: str):
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = User(**row)
            session.add(user)
    await session.commit()
