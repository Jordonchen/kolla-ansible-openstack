# Copyright 2016 Isaku Yamahata <isaku.yamahata at gmail.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""add sequence number to journal

Revision ID: 3d560427d776
Revises: 703dbf02afde
Create Date: 2016-08-05 15:50:22.151078

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3d560427d776'
down_revision = '703dbf02afde'


def upgrade():
    op.create_table(
        'opendaylightjournal_new',
        sa.Column('seqnum', sa.BigInteger(),
                  primary_key=True, autoincrement=True),
        sa.Column('object_type', sa.String(36), nullable=False),
        sa.Column('object_uuid', sa.String(36), nullable=False),
        sa.Column('operation', sa.String(36), nullable=False),
        sa.Column('data', sa.PickleType, nullable=True),
        sa.Column('state',
                  sa.Enum('pending', 'processing', 'failed', 'completed',
                          name='state'),
                  nullable=False, default='pending'),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('last_retried', sa.TIMESTAMP, server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )
