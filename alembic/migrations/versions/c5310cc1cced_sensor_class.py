"""sensor_class

Revision ID: c5310cc1cced
Revises: 89fe79911c77
Create Date: 2025-03-25 14:50:41.511155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga


# revision identifiers, used by Alembic.
revision: str = 'c5310cc1cced'
down_revision: Union[str, None] = '89fe79911c77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sensor_classes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('vessel_type_required_sensor_types',
    sa.Column('vessel_type_id', sa.Integer(), nullable=False),
    sa.Column('sensor_class_id', sa.Integer(), nullable=False),
    sa.Column('required', sa.Boolean(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['sensor_class_id'], ['sensor_classes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vessel_type_id'], ['vessel_types.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('vessel_type_id', 'sensor_class_id')
    )
    op.add_column('sensor_types', sa.Column('sensor_class_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'sensor_types', 'sensor_classes', ['sensor_class_id'], ['id'], ondelete='RESTRICT')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'sensor_types', type_='foreignkey')
    op.drop_column('sensor_types', 'sensor_class_id')
    op.drop_table('vessel_type_required_sensor_types')
    op.drop_table('sensor_classes')
    # ### end Alembic commands ###
