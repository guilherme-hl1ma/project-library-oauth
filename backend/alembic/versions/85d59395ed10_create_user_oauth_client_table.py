"""create user_oauth_client table

Revision ID: 85d59395ed10
Revises: a96e03a4e98d
Create Date: 2026-01-25 00:44:13.653134

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "85d59395ed10"
down_revision: Union[str, Sequence[str], None] = "a96e03a4e98d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_oauth_client",
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column(
            "client_id",
            sa.String(),
            sa.ForeignKey("oauth_client.client_id"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(), server_default="admin"),
    )


def downgrade() -> None:
    op.drop_table("user_oauth_client")
