"""create scope table

Revision ID: 5a4323320e2a
Revises: 070c3e00f3bd
Create Date: 2026-01-21 21:12:56.336667

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5a4323320e2a"
down_revision: Union[str, Sequence[str], None] = "070c3e00f3bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scope",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), unique=True),
        sa.Column("description", sa.String()),
    )


def downgrade() -> None:
    op.drop_table("scope")
