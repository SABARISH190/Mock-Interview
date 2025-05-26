"""Add last_seen to User

Revision ID: 1a2b3c4d5e6f
Revises: 64d6a1bcceb6
Create Date: 2025-05-24 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = '64d6a1bcceb6'
branch_labels = None
depends_on = None

def upgrade():
    # Add last_seen column with default value of current time
    op.add_column('users', 
        sa.Column('last_seen', 
                 sa.DateTime(), 
                 server_default=func.now(),
                 nullable=False)
    )

def downgrade():
    # Remove the last_seen column
    op.drop_column('users', 'last_seen')
