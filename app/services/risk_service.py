from typing import List, Dict, Optional
from datetime import datetime
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, cast, text
from sqlalchemy import String
from sqlalchemy.orm import selectinload

from app.models.risk import Risk, RiskStatus, RiskSeverity, RiskType
from app.models.shipment import Shipment
from app.schemas.risk import RiskCreate, RiskUpdate

class RiskService:
    """Service for risk detection and management"""

    # ------------------------------
    # Query endpoints
    # ------------------------------

    async def get_risks(
        self,
        skip: int,
        limit: int,
        shipment_id: Optional[int],
        status: Optional[str],
        severity: Optional[str],
        session: AsyncSession,
    ) -> List[Risk]:
        """Get risks with optional filters"""
        conditions = []
        if shipment_id is not None:
            conditions.append(Risk.shipment_id == shipment_id)
        if status is not None:
            # Normalize status to lowercase and compare the DB enum as text
            status_norm = status.lower()
            conditions.append(cast(Risk.status, String) == status_norm)
        if severity is not None:
            try:
                conditions.append(Risk.severity == RiskSeverity[severity.upper()])
            except KeyError:
                conditions.append(Risk.severity == severity)

        stmt = select(Risk).where(and_(*conditions)) if conditions else select(Risk)
        stmt = stmt.order_by(Risk.detected_at.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_risk(self, risk_id: int, session: AsyncSession) -> Optional[Risk]:
        """Get a single risk by id"""
        return await session.get(Risk, risk_id)

    async def get_shipment_risks(self, shipment_id: int, session: AsyncSession) -> List[Risk]:
        """Get all risks for a shipment"""
        result = await session.execute(
            select(Risk)
            .where(Risk.shipment_id == shipment_id)
            .order_by(Risk.detected_at.desc())
        )
        return result.scalars().all()

    async def get_risk_statistics(self, session: AsyncSession) -> Dict[str, int]:
        """Return simple dashboard stats"""
        total = await session.execute(select(func.count(Risk.id)))
        detected = await session.execute(select(func.count(Risk.id)).where(cast(Risk.status, String) == RiskStatus.DETECTED.value))
        resolved = await session.execute(select(func.count(Risk.id)).where(cast(Risk.status, String) == RiskStatus.RESOLVED.value))
        high = await session.execute(select(func.count(Risk.id)).where(Risk.severity == RiskSeverity.HIGH))
        critical = await session.execute(select(func.count(Risk.id)).where(Risk.severity == RiskSeverity.CRITICAL))
        return {
            "total": total.scalar_one(),
            "detected": detected.scalar_one(),
            "resolved": resolved.scalar_one(),
            "high": high.scalar_one(),
            "critical": critical.scalar_one(),
        }

    # ------------------------------
    # Mutations
    # ------------------------------

    async def create_risk(self, data: RiskCreate, session: AsyncSession) -> Risk:
        """Create risk from schema"""
        # Map to enums if needed
        # Normalize incoming enums/strings to the enum .value (lowercase string)
        if isinstance(data.risk_type, RiskType):
            rtype_val = data.risk_type.value
        else:
            try:
                rtype_val = RiskType[data.risk_type.upper()].value
            except Exception:
                try:
                    rtype_val = RiskType(data.risk_type).value
                except Exception:
                    rtype_val = RiskType.OTHER.value

        if isinstance(data.severity, RiskSeverity):
            sev_val = data.severity.value
        else:
            try:
                sev_val = RiskSeverity[data.severity.upper()].value
            except Exception:
                try:
                    sev_val = RiskSeverity(data.severity).value
                except Exception:
                    sev_val = RiskSeverity.MEDIUM.value

        risk = Risk(
            shipment_id=data.shipment_id,
            risk_type=rtype_val,
            severity=sev_val,
            description=data.description,
            confidence=data.confidence,
            detected_at=datetime.utcnow(),
            status=RiskStatus.DETECTED.value,
            expected_delay_hours=data.expected_delay_hours,
            risk_metadata=data.risk_metadata or {},  # align with DB column name
        )
        session.add(risk)
        await session.commit()
        await session.refresh(risk)

        # Update shipment flags
        await self._update_shipment_risk_flags(risk.shipment_id, session)
        return risk

    async def update_risk(self, risk_id: int, update: RiskUpdate, session: AsyncSession) -> Optional[Risk]:
        """Update risk from schema"""
        risk = await session.get(Risk, risk_id)
        if not risk:
            return None

        if update.description is not None:
            risk.description = update.description
        if update.confidence is not None:
            risk.confidence = update.confidence
        if update.status is not None:
            try:
                risk.status = RiskStatus[update.status.upper()].value
            except Exception:
                try:
                    # If provided already a value-like string
                    risk.status = RiskStatus(update.status).value
                except Exception:
                    risk.status = update.status
            if (getattr(risk.status, "value", str(risk.status)).lower()) == RiskStatus.RESOLVED.value:
                risk.resolved_at = datetime.utcnow()
        if update.severity is not None:
            try:
                risk.severity = RiskSeverity[update.severity.upper()].value
            except Exception:
                try:
                    risk.severity = RiskSeverity(update.severity).value
                except Exception:
                    risk.severity = update.severity
        if update.expected_delay_hours is not None:
            risk.expected_delay_hours = update.expected_delay_hours
        if update.risk_metadata is not None:
            risk.risk_metadata = update.risk_metadata

        await session.commit()
        await session.refresh(risk)
        await self._update_shipment_risk_flags(risk.shipment_id, session)
        return risk

    async def delete_risk(self, risk_id: int, session: AsyncSession) -> bool:
        """Delete a risk"""
        risk = await session.get(Risk, risk_id)
        if not risk:
            return False
        shipment_id = risk.shipment_id
        await session.delete(risk)
        await session.commit()
        await self._update_shipment_risk_flags(shipment_id, session)
        return True

    async def apply_mitigation(self, risk_id: int, mitigation_data: Dict, session: AsyncSession) -> Optional[Risk]:
        """Apply a mitigation to a risk and record outcome"""
        risk = await session.get(Risk, risk_id)
        if not risk:
            return None

        # Persist mitigation details; align with columns seen in logs
        actions = mitigation_data.get("mitigation_actions")
        selected = mitigation_data.get("selected_mitigation")
        result = mitigation_data.get("mitigation_result")
        cost_impact = mitigation_data.get("expected_cost_impact")

        if actions is not None:
            risk.mitigation_actions = actions
        if selected is not None:
            risk.selected_mitigation = selected
        if result is not None:
            risk.mitigation_result = result
        if cost_impact is not None:
            risk.expected_cost_impact = cost_impact

        # Update status if result indicates success
        if result and isinstance(result, dict) and result.get("status") == "completed":
            risk.status = RiskStatus.RESOLVED.value
            risk.resolved_at = datetime.utcnow()

        await session.commit()
        await session.refresh(risk)
        await self._update_shipment_risk_flags(risk.shipment_id, session)
        return risk

    # ------------------------------
    # Detection and assessment
    # ------------------------------

    async def assess_shipment(self, shipment_id: int, session: AsyncSession) -> List[Risk]:
        """Run detection and persist any newly detected risks"""
        risks = await self.detect_risks(shipment_id, session)
        persisted: List[Risk] = []

        for r in risks:
            # Avoid duplicate DETECTED risks with same type and description for the shipment
            # Normalize candidate risk_type to a lowercase value string for comparisons/inserts
            candidate_rt = r.risk_type
            try:
                if isinstance(candidate_rt, RiskType):
                    candidate_rt_val = candidate_rt.value
                elif isinstance(candidate_rt, str):
                    try:
                        candidate_rt_val = RiskType[candidate_rt.upper()].value
                    except Exception:
                        try:
                            candidate_rt_val = RiskType(candidate_rt).value
                        except Exception:
                            candidate_rt_val = RiskType.OTHER.value
                else:
                    candidate_rt_val = RiskType.OTHER.value
            except Exception:
                candidate_rt_val = RiskType.OTHER.value

            # Fetch existing risks for the shipment with the same description/status,
            # then compare risk_type in Python to avoid DB enum vs varchar operator issues.
            exists_stmt = select(Risk).where(
                and_(
                    Risk.shipment_id == shipment_id,
                    Risk.description == r.description,
                    cast(Risk.status, String) == RiskStatus.DETECTED.value,
                )
            )
            try:
                existing = (await session.execute(exists_stmt)).scalars().all()
            except Exception as exc:
                print(f"[ERROR] assess_shipment fetch existing failed for shipment={shipment_id} description={r.description} error={exc}")
                continue

            duplicate = False
            for ex in existing:
                try:
                    # Normalize existing risk_type to value string
                    ex_rt = ex.risk_type
                    if isinstance(ex_rt, RiskType):
                        ex_val = ex_rt.value
                    else:
                        ex_val = str(ex_rt)
                    if ex_val.lower() == candidate_rt_val.lower():
                        duplicate = True
                        break
                except Exception:
                    continue
            if duplicate:
                continue

            # Ensure the Risk object being added uses normalized string values for enums
            try:
                # if r.risk_type is an enum member or name, coerce to its value
                if isinstance(r.risk_type, RiskType):
                    r.risk_type = r.risk_type.value
                elif isinstance(r.risk_type, str):
                    try:
                        r.risk_type = RiskType[r.risk_type.upper()].value
                    except Exception:
                        try:
                            r.risk_type = RiskType(r.risk_type).value
                        except Exception:
                            r.risk_type = candidate_rt_val
                else:
                    r.risk_type = candidate_rt_val
            except Exception:
                r.risk_type = candidate_rt_val

            # severity and status normalize
            try:
                if isinstance(r.severity, RiskSeverity):
                    r.severity = r.severity.value
                elif isinstance(r.severity, str):
                    try:
                        r.severity = RiskSeverity[r.severity.upper()].value
                    except Exception:
                        try:
                            r.severity = RiskSeverity(r.severity).value
                        except Exception:
                            r.severity = RiskSeverity.MEDIUM.value
                else:
                    r.severity = RiskSeverity.MEDIUM.value
            except Exception:
                r.severity = RiskSeverity.MEDIUM.value

            try:
                if isinstance(r.status, RiskStatus):
                    r.status = r.status.value
                elif isinstance(r.status, str):
                    try:
                        r.status = RiskStatus[r.status.upper()].value
                    except Exception:
                        try:
                            r.status = RiskStatus(r.status).value
                        except Exception:
                            r.status = RiskStatus.DETECTED.value
                else:
                    r.status = RiskStatus.DETECTED.value
            except Exception:
                r.status = RiskStatus.DETECTED.value

            # Use a raw INSERT with explicit casts to the Postgres enum types
            # to avoid SQLAlchemy bind-type coercion that may send enum names.
            try:
                insert_sql = text(
                    """
                    INSERT INTO risks
                        (shipment_id, risk_type, severity, status, description, confidence, detected_at, expected_delay_hours, risk_metadata, source)
                    VALUES
                        (:shipment_id, CAST(:risk_type AS risktype), CAST(:severity AS riskseverity), CAST(:status AS riskstatus), :description, :confidence, :detected_at, :expected_delay_hours, CAST(:risk_metadata AS json), :source)
                    RETURNING id
                    """
                )
                params = {
                    "shipment_id": r.shipment_id,
                    "risk_type": (r.risk_type or candidate_rt_val),
                    "severity": (r.severity or RiskSeverity.MEDIUM.value),
                    "status": (r.status or RiskStatus.DETECTED.value),
                    "description": r.description,
                    "confidence": r.confidence,
                    "detected_at": r.detected_at,
                    "expected_delay_hours": r.expected_delay_hours,
                    "risk_metadata": json.dumps(r.risk_metadata or {}),
                    "source": getattr(r, "source", None),
                }
                result = await session.execute(insert_sql, params)
                row = result.first()
                new_id = row[0] if row is not None else None
                if new_id:
                    await session.commit()
                    new_risk = await session.get(Risk, new_id)
                    persisted.append(new_risk)
                else:
                    # fallback: add to session normally
                    session.add(r)
                    persisted.append(r)
            except Exception as exc:
                await session.rollback()
                print(f"[ERROR] raw insert failed for shipment={shipment_id} description={r.description} error={exc}")
                # try falling back to ORM add
                try:
                    session.add(r)
                    persisted.append(r)
                except Exception:
                    continue

        if persisted:
            await session.commit()
            # refresh to get IDs
            for r in persisted:
                await session.refresh(r)
            await self._update_shipment_risk_flags(shipment_id, session)
        return persisted

    async def detect_risks(self, shipment_id: int, session: AsyncSession) -> List[Risk]:
        """Detect risks for a shipment"""
        risks: List[Risk] = []
        shipment = await session.get(Shipment, shipment_id)
        if not shipment:
            return risks

        # Ensure metadata dicts exist
        shipment_metadata = shipment.shipment_metadata or {}
        current_location = shipment.current_location

        # Port congestion
        risks.extend(await self._detect_port_congestion(shipment, session))

        # Customs delays
        customs_status = shipment_metadata.get("customs_status")
        risks.extend(await self._detect_customs_delays(customs_status, shipment, session))

        # Quality holds
        quality_status = shipment_metadata.get("quality_status")
        risks.extend(await self._detect_quality_holds(quality_status, shipment, session))

        # Delays
        risks.extend(await self._detect_delays(shipment, session))

        return risks

    async def _detect_port_congestion(self, shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect port congestion risks"""
        risks: List[Risk] = []
        if shipment.next_port:
            congestion_level = await self._get_congestion_level(shipment.next_port)
            if congestion_level > 0.7:
                risks.append(
                    Risk(
                        shipment_id=shipment.id,
                        risk_type=RiskType.PORT_CONGESTION.value,
                        severity=(RiskSeverity.HIGH.value if congestion_level > 0.8 else RiskSeverity.MEDIUM.value),
                        description=f"Port congestion detected at {shipment.next_port}",
                        confidence=congestion_level,
                        detected_at=datetime.utcnow(),
                        status=RiskStatus.DETECTED.value,
                        expected_delay_hours=congestion_level * 48,
                        risk_metadata={"port": shipment.next_port, "congestion_level": congestion_level},
                    )
                )
        return risks

    async def _detect_customs_delays(self, customs_status: Optional[str], shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect customs delay risks"""
        risks: List[Risk] = []
        if customs_status in {"delayed", "held", "under_review"}:
            risks.append(
                Risk(
                    shipment_id=shipment.id,
                    risk_type=RiskType.CUSTOMS_DELAY.value,
                    severity=RiskSeverity.HIGH.value,
                    description=f"Customs clearance {customs_status}",
                    confidence=0.85,
                    detected_at=datetime.utcnow(),
                    status=RiskStatus.DETECTED.value,
                    expected_delay_hours=24,
                    risk_metadata={"customs_status": customs_status},
                )
            )
        return risks

    async def _detect_quality_holds(self, quality_status: Optional[str], shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect quality hold risks"""
        risks: List[Risk] = []
        if quality_status in {"hold", "inspection"}:
            risks.append(
                Risk(
                    shipment_id=shipment.id,
                    risk_type=RiskType.QUALITY_HOLD.value,
                    severity=RiskSeverity.MEDIUM.value,
                    description=f"Quality inspection {quality_status}",
                    confidence=0.9,
                    detected_at=datetime.utcnow(),
                    status=RiskStatus.DETECTED.value,
                    expected_delay_hours=12,
                    risk_metadata={"quality_status": quality_status},
                )
            )
        return risks

    async def _detect_delays(self, shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect delay risks"""
        risks: List[Risk] = []
        if shipment.estimated_arrival and datetime.utcnow() > shipment.estimated_arrival:
            delay_hours = (datetime.utcnow() - shipment.estimated_arrival).total_seconds() / 3600
            if delay_hours > 4:
                risks.append(
                    Risk(
                        shipment_id=shipment.id,
                        risk_type=RiskType.OTHER.value,
                        severity=(RiskSeverity.HIGH.value if delay_hours > 24 else RiskSeverity.MEDIUM.value),
                        description=f"Shipment delayed by {delay_hours:.1f} hours",
                        confidence=min(0.9, delay_hours / 48),
                        detected_at=datetime.utcnow(),
                        status=RiskStatus.DETECTED.value,
                        expected_delay_hours=delay_hours,
                        risk_metadata={"delay_hours": delay_hours},
                    )
                )
        return risks

    async def _get_congestion_level(self, port_code: str) -> float:
        """Get congestion level for a port (stubbed)"""
        congestion_data = {
            "CNSHA": 0.8,
            "USLAX": 0.7,
            "SGSIN": 0.4,
            "NLRTM": 0.6,
        }
        return congestion_data.get(port_code, 0.3)

    # ------------------------------
    # Internal helpers
    # ------------------------------

    async def _update_shipment_risk_flags(self, shipment_id: int, session: AsyncSession) -> None:
        """Update shipment-level risk flags based on current risks"""
        shipment = await session.get(Shipment, shipment_id)
        if not shipment:
            return
        result = await session.execute(select(Risk).where(Risk.shipment_id == shipment_id))
        risks = result.scalars().all()
        if risks:
            shipment.risk_score = max(r.confidence or 0.0 for r in risks)
            # normalize status values for comparison
            shipment.is_at_risk = any((getattr(r.status, "value", str(r.status))).lower() == RiskStatus.DETECTED.value for r in risks)
            shipment.last_risk_check = datetime.utcnow()
        else:
            shipment.risk_score = 0.0
            shipment.is_at_risk = False
            shipment.last_risk_check = datetime.utcnow()
        await session.commit()

    async def update_risk_status(self, risk_id: int, status: RiskStatus, session: AsyncSession) -> Optional[Risk]:
        """Update risk status (legacy helper used elsewhere)"""
        risk = await session.get(Risk, risk_id)
        if risk:
            # accept either enum member or string
            if isinstance(status, RiskStatus):
                risk.status = status.value
            else:
                try:
                    risk.status = RiskStatus[status.upper()].value
                except Exception:
                    try:
                        risk.status = RiskStatus(status).value
                    except Exception:
                        risk.status = status

            if (getattr(risk.status, "value", str(risk.status)).lower()) == RiskStatus.RESOLVED.value:
                risk.resolved_at = datetime.utcnow()
            await session.commit()
            await session.refresh(risk)
            await self._update_shipment_risk_flags(risk.shipment_id, session)
        return risk
