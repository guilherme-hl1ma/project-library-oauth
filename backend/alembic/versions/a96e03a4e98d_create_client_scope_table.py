"""create client_scope table

Revision ID: a96e03a4e98d
Revises: 5a4323320e2a
Create Date: 2026-01-21 21:16:07.610431

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a96e03a4e98d"
down_revision: Union[str, Sequence[str], None] = "5a4323320e2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_scope",
        sa.Column("client_id", sa.String()),
        sa.Column("scope_id", sa.String()),
    )
    op.create_foreign_key(
        constraint_name="fk_client_id",
        source_table="client_scope",
        referent_table="oauth_client",
        local_cols=["client_id"],
        remote_cols=["client_id"],
    )
    op.create_foreign_key(
        constraint_name="fk_scope_id",
        source_table="client_scope",
        referent_table="scope",
        local_cols=["scope_id"],
        remote_cols=["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        constraint_name="fk_client_id", table_name="client_scope", type_="foreignkey"
    )
    op.drop_constraint(
        constraint_name="fk_scope_id", table_name="client_scope", type_="foreignkey"
    )
    op.drop_table("client_scope")
