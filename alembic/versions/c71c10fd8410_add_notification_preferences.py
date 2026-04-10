"""add notification preferences"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'c71c10fd8410'
down_revision: Union[str, Sequence[str], None] = 'new_revision_id'  # ⚠️ put your LAST migration ID here
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('email_on_new_application', sa.Boolean(), default=True),
        sa.Column('email_on_status_change', sa.Boolean(), default=True),
        sa.Column('in_app_notifications_enabled', sa.Boolean(), default=True),
        sa.Column('notification_frequency', sa.String(length=50)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime())
    )


def downgrade() -> None:
    op.drop_table('notification_preferences')