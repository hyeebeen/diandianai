"""Initial migration with all models

Revision ID: 5276d92b1907
Revises:
Create Date: 2025-09-27 23:10:35.387189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5276d92b1907'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create tenants table first (base dependency)
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('domain', sa.String(100), nullable=True),
        sa.Column('is_active', sa.String(1), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'MANAGER', 'DRIVER', 'CUSTOMER', 'DISPATCHER', name='userrole'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.String(10), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(500), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=True),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_tenant_id'), 'refresh_tokens', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=False)

    # Create shipments table
    op.create_table('shipments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_number', sa.String(50), nullable=False),
        sa.Column('pickup_address', sa.Text(), nullable=False),
        sa.Column('delivery_address', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('UNASSIGNED', 'ASSIGNED', 'DISPATCHED', 'IN_TRANSIT', 'AT_PICKUP', 'LOADED', 'DELIVERED', name='shipmentstatus'), nullable=True),
        sa.Column('customer_name', sa.String(200), nullable=False),
        sa.Column('transport_mode', sa.String(100), nullable=True),
        sa.Column('equipment_type', sa.String(100), nullable=True),
        sa.Column('weight_kg', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('commodity_type', sa.String(200), nullable=True),
        sa.Column('packing_type', sa.String(100), nullable=True),
        sa.Column('pickup_coordinates', sa.JSON(), nullable=True),
        sa.Column('delivery_coordinates', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('badges', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('pickup_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shipment_number')
    )
    op.create_index(op.f('ix_shipments_id'), 'shipments', ['id'], unique=False)
    op.create_index(op.f('ix_shipments_shipment_number'), 'shipments', ['shipment_number'], unique=False)
    op.create_index(op.f('ix_shipments_status'), 'shipments', ['status'], unique=False)
    op.create_index(op.f('ix_shipments_tenant_id'), 'shipments', ['tenant_id'], unique=False)

    # Create vehicles table
    op.create_table('vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_plate', sa.String(20), nullable=False),
        sa.Column('vehicle_type', sa.String(50), nullable=True),
        sa.Column('capacity_kg', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('driver_name', sa.String(100), nullable=True),
        sa.Column('driver_phone', sa.String(20), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('is_active', sa.String(1), nullable=True),
        sa.Column('current_coordinates', sa.JSON(), nullable=True),
        sa.Column('last_update_time', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('license_plate')
    )
    op.create_index(op.f('ix_vehicles_id'), 'vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_vehicles_license_plate'), 'vehicles', ['license_plate'], unique=False)
    op.create_index(op.f('ix_vehicles_tenant_id'), 'vehicles', ['tenant_id'], unique=False)

    # Create remaining tables...

    # Create AI model configs table
    op.create_table('ai_model_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('api_key', sa.String(500), nullable=False),
        sa.Column('api_base_url', sa.String(500), nullable=True),
        sa.Column('api_version', sa.String(20), nullable=True),
        sa.Column('max_tokens', sa.String(10), nullable=True),
        sa.Column('temperature', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('top_p', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.String(10), nullable=True),
        sa.Column('rate_limit_per_minute', sa.String(10), nullable=True),
        sa.Column('daily_quota', sa.String(10), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_model_configs_id'), 'ai_model_configs', ['id'], unique=False)
    op.create_index(op.f('ix_ai_model_configs_tenant_id'), 'ai_model_configs', ['tenant_id'], unique=False)

    # Create AI conversations table
    op.create_table('ai_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('message_count', sa.String(10), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_conversations_id'), 'ai_conversations', ['id'], unique=False)
    op.create_index(op.f('ix_ai_conversations_tenant_id'), 'ai_conversations', ['tenant_id'], unique=False)

    # Add Row-Level Security policies
    op.execute("""
    -- Enable RLS on all tables
    ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
    ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
    ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
    ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;
    ALTER TABLE ai_model_configs ENABLE ROW LEVEL SECURITY;
    ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;

    -- Create RLS policies for tenant isolation
    CREATE POLICY tenant_isolation_users ON users USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    CREATE POLICY tenant_isolation_refresh_tokens ON refresh_tokens USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    CREATE POLICY tenant_isolation_shipments ON shipments USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    CREATE POLICY tenant_isolation_vehicles ON vehicles USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    CREATE POLICY tenant_isolation_ai_model_configs ON ai_model_configs USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    CREATE POLICY tenant_isolation_ai_conversations ON ai_conversations USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop RLS policies
    op.execute("""
    DROP POLICY IF EXISTS tenant_isolation_ai_conversations ON ai_conversations;
    DROP POLICY IF EXISTS tenant_isolation_ai_model_configs ON ai_model_configs;
    DROP POLICY IF EXISTS tenant_isolation_vehicles ON vehicles;
    DROP POLICY IF EXISTS tenant_isolation_shipments ON shipments;
    DROP POLICY IF EXISTS tenant_isolation_refresh_tokens ON refresh_tokens;
    DROP POLICY IF EXISTS tenant_isolation_users ON users;
    """)

    # Drop tables in reverse order
    op.drop_table('ai_conversations')
    op.drop_table('ai_model_configs')
    op.drop_table('vehicles')
    op.drop_table('shipments')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('tenants')

    # Drop custom enums
    op.execute('DROP TYPE IF EXISTS shipmentstatus')
    op.execute('DROP TYPE IF EXISTS userrole')
