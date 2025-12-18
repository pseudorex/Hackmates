"""add bio column to users

Revision ID: a01b66751351
Revises: 2966fbf7be83
Create Date: 2025-12-15 22:27:52.190080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a01b66751351'
down_revision: Union[str, Sequence[str], None] = '2966fbf7be83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('bio', sa.String(), nullable=True))
    pass


def downgrade() -> None:
    op.drop_column('users', 'bio')
    pass
