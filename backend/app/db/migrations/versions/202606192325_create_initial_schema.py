"""create_initial_schema

Revision ID: initial_schema_001
Revises: 
Create Date: 2026-06-19 23:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'initial_schema_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Table: users
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('noti_daily', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Table: papers
    op.create_table(
        'papers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('arxiv_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('authors', sa.JSON(), nullable=True),
        sa.Column('published', sa.Date(), nullable=True),
        sa.Column('pdf_path', sa.String(length=500), nullable=True),
        sa.Column('score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('has_audio', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_papers_arxiv_id'), 'papers', ['arxiv_id'], unique=True)
    op.create_index(op.f('ix_papers_published'), 'papers', ['published'], unique=False)
    op.create_index(op.f('ix_papers_score'), 'papers', ['score'], unique=False)
    op.create_index('idx_papers_created_at', 'papers', ['created_at'], unique=False)

    # 3. Table: digests
    op.create_table(
        'digests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('digest_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_digests_digest_date'), 'digests', ['digest_date'], unique=True)

    # 4. Table: digest_papers
    op.create_table(
        'digest_papers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('digest_id', sa.BigInteger(), nullable=False),
        sa.Column('paper_id', sa.BigInteger(), nullable=False),
        sa.Column('rank_position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['digest_id'], ['digests.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('digest_id', 'paper_id', name='uq_digest_paper'),
        sa.UniqueConstraint('digest_id', 'rank_position', name='uq_digest_rank'),
        sa.CheckConstraint('rank_position BETWEEN 1 AND 5', name='chk_rank_position')
    )
    op.create_index('idx_digest_papers_digest_id', 'digest_papers', ['digest_id'], unique=False)
    op.create_index('idx_digest_papers_paper_id', 'digest_papers', ['paper_id'], unique=False)
    op.create_index('idx_digest_papers_rank_position', 'digest_papers', ['rank_position'], unique=False)

    # 5. Table: audio_abstracts
    op.create_table(
        'audio_abstracts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('paper_id', sa.BigInteger(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('paper_timestamps', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', name='uq_audio_abstracts_paper_id')
    )

    # 6. Table: chat_sessions
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('paper_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'], unique=False)
    op.create_index('idx_chat_sessions_paper_id', 'chat_sessions', ['paper_id'], unique=False)

    # 7. Table: chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('chat_session_id', sa.BigInteger(), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='chat_message_role_enum'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tts_path', sa.String(length=500), nullable=True),
        sa.Column('tts_timestamps', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['chat_session_id'], unique=False)
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'], unique=False)

    # 8. Table: topics
    op.create_table(
        'topics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topics_name'), 'topics', ['name'], unique=True)

    # 9. Table: paper_topics
    op.create_table(
        'paper_topics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('paper_id', sa.BigInteger(), nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', 'topic_id', name='uq_paper_topic'),
        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='chk_confidence_score')
    )
    op.create_index('idx_paper_topics_paper_id', 'paper_topics', ['paper_id'], unique=False)
    op.create_index('idx_paper_topics_topic_id', 'paper_topics', ['topic_id'], unique=False)

    # 10. Table: notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('digest_id', sa.BigInteger(), nullable=False),
        sa.Column('channel', sa.Enum('email', 'web', 'system', name='notification_channel_enum'), nullable=False, server_default='email'),
        sa.Column('status', sa.Enum('pending', 'sent', 'failed', name='notification_status_enum'), nullable=False, server_default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['digest_id'], ['digests.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'digest_id', 'channel', name='uq_user_digest_channel')
    )
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('idx_notifications_digest_id', 'notifications', ['digest_id'], unique=False)
    op.create_index('idx_notifications_status', 'notifications', ['status'], unique=False)
    op.create_index('idx_notifications_sent_at', 'notifications', ['sent_at'], unique=False)


def downgrade():
    op.drop_table('notifications')
    op.drop_table('paper_topics')
    op.drop_index(op.f('ix_topics_name'), table_name='topics')
    op.drop_table('topics')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('audio_abstracts')
    op.drop_table('digest_papers')
    op.drop_index(op.f('ix_digests_digest_date'), table_name='digests')
    op.drop_table('digests')
    op.drop_table('papers')
    op.drop_table('users')
    
    # Drop custom enum types for clean state in databases like PostgreSQL, but MySQL maps Enums directly.
    # MySQL automatically drops column metadata with table, so no explicit Enum drop is required.
