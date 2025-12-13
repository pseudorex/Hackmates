"""drop role and phone_number from users

Revision ID: 2966fbf7be83
Revises: 31b479fd7374
Create Date: 2025-12-13 21:32:00.676136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2966fbf7be83'
down_revision: Union[str, Sequence[str], None] = '31b479fd7374'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "role")
    op.drop_column("users", "phone_number")


def downgrade():
    op.add_column(
        "users",
        sa.Column("phone_number", sa.String(), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("role", sa.String(), nullable=True)
    )
