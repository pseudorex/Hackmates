"""Add post_image table and remove photo column

Revision ID: df8a91f19616
Revises: 5244618da2e2
Create Date: 2026-01-13 21:15:17.587626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df8a91f19616'
down_revision: Union[str, Sequence[str], None] = '5244618da2e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'post_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['post_id'],
            ['posts.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.drop_column('posts', 'photo')



def downgrade():
    op.add_column(
        'posts',
        sa.Column('photo', sa.String(), nullable=True)
    )

    op.drop_table('post_images')

