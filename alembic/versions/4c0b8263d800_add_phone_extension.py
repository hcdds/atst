"""Add Phone Extension

Revision ID: 4c0b8263d800
Revises: e1081cf01780
Create Date: 2018-10-29 11:14:01.332665

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c0b8263d800'
down_revision = 'e1081cf01780'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('request_reviews', sa.Column('phone_ext_mao', sa.String(), nullable=True))
    op.add_column('request_revisions', sa.Column('phone_ext', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone_ext', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'phone_ext')
    op.drop_column('request_revisions', 'phone_ext')
    op.drop_column('request_reviews', 'phone_ext_mao')
    # ### end Alembic commands ###
