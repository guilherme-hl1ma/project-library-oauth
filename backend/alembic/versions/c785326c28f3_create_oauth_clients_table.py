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
        sa.Column("client_secret", sa.String(255), nullable=False),
        sa.Column("redirect_uris", sa.Text(), nullable=False),
        sa.Column("client_name", sa.String(100), nullable=True),
        sa.Column("grant_types", sa.String(200), server_default="authorization_code"),
        sa.Column(
            "registration_access_token", sa.String(255), nullable=True, index=True
        ),
        sa.Column("issued_at", sa.Integer(), nullable=False),
        sa.Column("software_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )


def downgrade() -> None:
    op.drop_table("oauth_client")
