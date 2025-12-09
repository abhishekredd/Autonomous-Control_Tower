"""Initial migration

Revision ID: 001_initial_migration
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create shipments table
    op.create_table('shipments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracking_number', sa.String(), nullable=True),
        sa.Column('reference_number', sa.String(), nullable=True),
        sa.Column('origin', sa.String(), nullable=False),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('current_location', sa.String(), nullable=True),
        sa.Column('current_port', sa.String(), nullable=True),
        sa.Column('next_port', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_TRANSIT', 'DELAYED', 'ARRIVED', 'CANCELLED', 'DIVERTED', name='shipmentstatus'), nullable=True),
        sa.Column('mode', sa.Enum('AIR', 'SEA', 'LAND', 'RAIL', 'MULTIMODAL', name='shipmentmode'), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('estimated_departure', sa.DateTime(), nullable=True),
        sa.Column('estimated_arrival', sa.DateTime(), nullable=True),
        sa.Column('actual_departure', sa.DateTime(), nullable=True),
        sa.Column('actual_arrival', sa.DateTime(), nullable=True),
        sa.Column('shipper', sa.String(), nullable=True),
        sa.Column('carrier', sa.String(), nullable=True),
        sa.Column('consignee', sa.String(), nullable=True),
        sa.Column('customs_broker', sa.String(), nullable=True),
        sa.Column('is_at_risk', sa.Boolean(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('last_risk_check', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for shipments
    op.create_index(op.f('ix_shipments_id'), 'shipments', ['id'], unique=False)
    op.create_index(op.f('ix_shipments_reference_number'), 'shipments', ['reference_number'], unique=False)
    op.create_index(op.f('ix_shipments_tracking_number'), 'shipments', ['tracking_number'], unique=True)
    
    # Create shipment_events table
    op.create_table('shipment_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for shipment_events
    op.create_index(op.f('ix_shipment_events_id'), 'shipment_events', ['id'], unique=False)
    op.create_index(op.f('ix_shipment_events_shipment_id'), 'shipment_events', ['shipment_id'], unique=False)
    
    # Create shipment_routes table
    op.create_table('shipment_routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=True),
        sa.Column('route_type', sa.String(), nullable=True),
        sa.Column('waypoints', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_distance', sa.Float(), nullable=True),
        sa.Column('estimated_duration', sa.Float(), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for shipment_routes
    op.create_index(op.f('ix_shipment_routes_id'), 'shipment_routes', ['id'], unique=False)
    op.create_index(op.f('ix_shipment_routes_shipment_id'), 'shipment_routes', ['shipment_id'], unique=False)
    
    # Create risks table
    op.create_table('risks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=True),
        sa.Column('risk_type', sa.Enum('PORT_CONGESTION', 'CUSTOMS_DELAY', 'QUALITY_HOLD', 'WEATHER_IMPACT', 'EQUIPMENT_FAILURE', 'LABOR_STRIKE', 'SECURITY_ISSUE', 'ROUTE_BLOCKAGE', 'CAPACITY_SHORTAGE', 'OTHER', name='risktype'), nullable=True),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='riskseverity'), nullable=True),
        sa.Column('status', sa.Enum('DETECTED', 'ANALYZING', 'MITIGATING', 'RESOLVED', 'ESCALATED', name='riskstatus'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('expected_delay_hours', sa.Float(), nullable=True),
        sa.Column('expected_cost_impact', sa.Float(), nullable=True),
        sa.Column('affected_parties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mitigation_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('selected_mitigation', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mitigation_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for risks
    op.create_index(op.f('ix_risks_id'), 'risks', ['id'], unique=False)
    op.create_index(op.f('ix_risks_shipment_id'), 'risks', ['shipment_id'], unique=False)
    
    # Create simulations table
    op.create_table('simulations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=True),
        sa.Column('simulation_type', sa.Enum('MITIGATION_ANALYSIS', 'ROUTE_OPTIMIZATION', 'WHAT_IF_SCENARIO', 'COST_BENEFIT', name='simulationtype'), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='simulationstatus'), nullable=True),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scenario_description', sa.Text(), nullable=True),
        sa.Column('results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('best_option', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('initiated_by', sa.String(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for simulations
    op.create_index(op.f('ix_simulations_id'), 'simulations', ['id'], unique=False)
    op.create_index(op.f('ix_simulations_shipment_id'), 'simulations', ['shipment_id'], unique=False)

def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_simulations_shipment_id'), table_name='simulations')
    op.drop_index(op.f('ix_simulations_id'), table_name='simulations')
    op.drop_table('simulations')
    
    op.drop_index(op.f('ix_risks_shipment_id'), table_name='risks')
    op.drop_index(op.f('ix_risks_id'), table_name='risks')
    op.drop_table('risks')
    
    op.drop_index(op.f('ix_shipment_routes_shipment_id'), table_name='shipment_routes')
    op.drop_index(op.f('ix_shipment_routes_id'), table_name='shipment_routes')
    op.drop_table('shipment_routes')
    
    op.drop_index(op.f('ix_shipment_events_shipment_id'), table_name='shipment_events')
    op.drop_index(op.f('ix_shipment_events_id'), table_name='shipment_events')
    op.drop_table('shipment_events')
    
    op.drop_index(op.f('ix_shipments_tracking_number'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_reference_number'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_id'), table_name='shipments')
    op.drop_table('shipments')
    
    # Drop enums
    op.execute('DROP TYPE shipmentstatus')
    op.execute('DROP TYPE shipmentmode')
    op.execute('DROP TYPE risktype')
    op.execute('DROP TYPE riskseverity')
    op.execute('DROP TYPE riskstatus')
    op.execute('DROP TYPE simulationtype')
    op.execute('DROP TYPE simulationstatus')