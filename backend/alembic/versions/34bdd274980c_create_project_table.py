"""create project table

Revision ID: 34bdd274980c
Revises: 85d59395ed10
Create Date: 2026-02-11 21:28:18.405517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34bdd274980c'
down_revision: Union[str, Sequence[str], None] = '85d59395ed10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("project")
