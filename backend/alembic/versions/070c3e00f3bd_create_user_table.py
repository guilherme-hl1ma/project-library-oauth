"""create user table

Revision ID: 070c3e00f3bd
Revises: c785326c28f3
Create Date: 2026-01-21 21:00:10.364055

"""

from enum import unique
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "070c3e00f3bd"
down_revision: Union[str, Sequence[str], None] = "c785326c28f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="user_role"),
            nullable=False,
            server_default="user",
        ),
    )


def downgrade() -> None:
    op.drop_table("user")
