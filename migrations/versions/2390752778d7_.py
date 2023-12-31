"""empty message

Revision ID: 2390752778d7
Revises: 15301c20409a
Create Date: 2023-06-15 23:09:46.342015

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2390752778d7'
down_revision = '15301c20409a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('achievements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('body', sa.String(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('achievements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_achievements_timestamp'), ['timestamp'], unique=False)

    with op.batch_alter_table('news', schema=None) as batch_op:
        batch_op.drop_column('deleted')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('news', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted', sa.BOOLEAN(), nullable=True))

    with op.batch_alter_table('achievements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_achievements_timestamp'))

    op.drop_table('achievements')
    # ### end Alembic commands ###
