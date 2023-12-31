"""empty message

Revision ID: dc8ae2754936
Revises: e6490bda4004
Create Date: 2023-06-05 01:00:33.556973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc8ae2754936'
down_revision = 'e6490bda4004'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('manure', schema=None) as batch_op:
        batch_op.add_column(sa.Column('in_stock', sa.Boolean(), nullable=True))
        batch_op.drop_column('is_stock')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('manure', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_stock', sa.BOOLEAN(), nullable=True))
        batch_op.drop_column('in_stock')

    # ### end Alembic commands ###
