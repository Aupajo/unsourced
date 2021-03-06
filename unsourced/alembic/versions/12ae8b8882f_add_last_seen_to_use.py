"""add last_seen to user

Revision ID: 12ae8b8882f
Revises: 2480008ebdce
Create Date: 2012-07-04 10:54:55.579362

"""

# revision identifiers, used by Alembic.
revision = '12ae8b8882f'
down_revision = '2480008ebdce'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('useraccount', sa.Column('last_seen', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('useraccount', 'last_seen')
    ### end Alembic commands ###
