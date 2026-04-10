from alembic import op
import sqlalchemy as sa

revision = 'new_revision_id'
down_revision = 'd92060600e93'
branch_labels = None
depends_on = None


def upgrade():

    # ✅ STEP 1: Create ENUM
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationtype AS ENUM (
                'NEW_APPLICATION',
                'APPLICATION_APPROVED',
                'APPLICATION_REJECTED',
                'APPLICATION_SHORTLISTED',
                'MESSAGE_RECEIVED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ✅ STEP 2: Add column
    op.add_column('notifications', sa.Column(
        'notification_type',
        sa.Enum(
            'NEW_APPLICATION',
            'APPLICATION_APPROVED',
            'APPLICATION_REJECTED',
            'APPLICATION_SHORTLISTED',
            'MESSAGE_RECEIVED',
            name='notificationtype'
        ),
        nullable=True   # 🔥 important (temporary)
    ))

    # other columns
    op.add_column('notifications', sa.Column('description', sa.String(500), nullable=True))
    op.add_column('notifications', sa.Column('action_url', sa.String(500), nullable=True))
    op.add_column('notifications', sa.Column('metadata', sa.JSON(), nullable=True))
    op.add_column('notifications', sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('notifications', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))

    op.drop_column('notifications', 'message')


    # post_responses
    op.add_column('post_responses', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('post_responses', sa.Column('reviewed_by', sa.Integer(), nullable=True))
    op.add_column('post_responses', sa.Column('owner_response_message', sa.Text(), nullable=True))

    op.create_foreign_key(
        None,
        'post_responses',
        'users',
        ['reviewed_by'],
        ['id']
    )


    # posts
    op.add_column('posts', sa.Column('application_count', sa.Integer(), nullable=True))


def downgrade():

    op.drop_column('posts', 'application_count')

    op.drop_constraint(None, 'post_responses', type_='foreignkey')
    op.drop_column('post_responses', 'owner_response_message')
    op.drop_column('post_responses', 'reviewed_by')
    op.drop_column('post_responses', 'reviewed_at')

    op.add_column('notifications', sa.Column('message', sa.VARCHAR(500), nullable=False))

    op.drop_column('notifications', 'expires_at')
    op.drop_column('notifications', 'read_at')
    op.drop_column('notifications', 'metadata')
    op.drop_column('notifications', 'action_url')
    op.drop_column('notifications', 'description')
    op.drop_column('notifications', 'notification_type')

    # drop enum
    op.execute("DROP TYPE IF EXISTS notificationtype")