"""add mobile to users

Revision ID: d92060600e93
Revises: 9353cc675683
Create Date: 2026-03-29 17:24:02.783378
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd92060600e93'
down_revision: Union[str, Sequence[str], None] = '9353cc675683'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('mobile', sa.String(length=15), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'mobile')