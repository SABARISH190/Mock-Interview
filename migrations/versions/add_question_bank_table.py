"""Add question_bank table

Revision ID: 123456789abc
Revises: 64d6a1bcceb6
Create Date: 2025-05-22 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '123456789abc'
down_revision = '64d6a1bcceb6'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('question_bank',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=50), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_question_bank_domain'), 'question_bank', ['domain'], unique=False)
    op.create_index(op.f('ix_question_bank_question_type'), 'question_bank', ['question_type'], unique=False)
    op.create_index(op.f('ix_question_bank_difficulty'), 'question_bank', ['difficulty'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_question_bank_difficulty'), table_name='question_bank')
    op.drop_index(op.f('ix_question_bank_question_type'), table_name='question_bank')
    op.drop_index(op.f('ix_question_bank_domain'), table_name='question_bank')
    op.drop_table('question_bank')
