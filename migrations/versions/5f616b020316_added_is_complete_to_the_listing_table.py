"""added is_complete to the Listing table

Revision ID: 5f616b020316
Revises: bbaf0300d682
Create Date: 2019-11-10 21:46:44.041179

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f616b020316'
down_revision = 'bbaf0300d682'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('listing', sa.Column('is_complete', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('listing', 'is_complete')
    # ### end Alembic commands ###
