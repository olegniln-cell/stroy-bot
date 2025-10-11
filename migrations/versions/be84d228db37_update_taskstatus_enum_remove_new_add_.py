"""Update taskstatus enum: remove new, add approved/rework

Revision ID: be84d228db37
Revises: 711c8b8f6276
Create Date: 2025-10-11 14:51:10.685447

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "be84d228db37"
down_revision: Union[str, Sequence[str], None] = "711c8b8f6276"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'approved';")
    op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'rework';")


def downgrade():
    pass
