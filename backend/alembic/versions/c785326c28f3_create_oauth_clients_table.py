"""create oauth_clients table

Revision ID: c785326c28f3
Revises:
Create Date: 2026-01-21 20:34:24.232309

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c785326c28f3"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oauth_client",
        sa.Column("client_id", sa.String(), primary_key=True),
        sa.Column("secret", sa.String(50), nullable=False),
        sa.Column("redirect_uri", sa.Unicode(200), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("oauth_client")
