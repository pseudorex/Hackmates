from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9353cc675683"
down_revision = "df8a91f19616"
branch_labels = None
depends_on = None


def upgrade():
    # Index for ordering feed by time
    op.create_index(
        "idx_posts_created_at",
        "posts",
        ["created_at"],
        postgresql_using="btree"
    )

    # Index for filtering active posts
    op.create_index(
        "idx_posts_is_active",
        "posts",
        ["is_active"]
    )

    # Composite index for user-specific feeds
    op.create_index(
        "idx_posts_created_by_created_at",
        "posts",
        ["created_by", "created_at"],
        postgresql_using="btree"
    )


def downgrade():
    op.drop_index(
        "idx_posts_created_by_created_at",
        table_name="posts"
    )
    op.drop_index(
        "idx_posts_is_active",
        table_name="posts"
    )
    op.drop_index(
        "idx_posts_created_at",
        table_name="posts"
    )
