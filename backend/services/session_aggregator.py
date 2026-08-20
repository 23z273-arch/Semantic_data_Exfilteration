"""
services/session_aggregator.py — Stage-3 multi-turn session risk tracking.

Maintains a sliding-window of per-turn risk scores per session.
Escalates decision when cumulative score crosses threshold,
defending against piecemeal reconstruction attacks (AT-06).
"""
import logging
import time
from dataclasses import dataclass, field
from statistics import mean
from typing import List, Set

from config import settings

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 3600   # 1 hour of inactivity = session expired


@dataclass
class SessionState:
    session_id: str
    risk_history: List[float] = field(default_factory=list)
    accumulated_tags: Set[str] = field(default_factory=set)
    turn_number: int = 0
    cumulative_score: float = 0.0
    escalated: bool = False
    last_updated: float = field(default_factory=time.time)


class SessionAggregator:
    """
    In-process session state store.
    Production systems should replace _sessions with a Redis backend.
    """

    def __init__(
        self,
        window_size: int = settings.SESSION_WINDOW_SIZE,
        block_threshold: float = settings.SESSION_BLOCK_THRESHOLD,
        escalation_multiplier: float = settings.SESSION_ESCALATION_MULTIPLIER,
    ):
        self._sessions: dict[str, SessionState] = {}
        self.window_size = window_size
        self.block_threshold = block_threshold
        self.escalation_multiplier = escalation_multiplier

    # ── Public API ────────────────────────────────────────────────────────────

    def update(
        self,
        session_id: str,
        turn_risk_score: float,
        lineage_tags: List[str],
    ) -> SessionState:
        """
        Record a new turn's risk score and update cumulative state.
        Returns the updated SessionState.
        """
        self._evict_stale()

        state = self._sessions.get(session_id)
        if state is None:
            state = SessionState(session_id=session_id)
            self._sessions[session_id] = state

        state.turn_number += 1
        state.risk_history.append(turn_risk_score)
        # Keep only last N turns
        state.risk_history = state.risk_history[-self.window_size:]
        state.accumulated_tags.update(lineage_tags)
        state.cumulative_score = mean(state.risk_history) if state.risk_history else 0.0
        state.last_updated = time.time()

        if state.cumulative_score >= self.block_threshold and not state.escalated:
            state.escalated = True
            logger.warning(
                "Session %s ESCALATED — cumulative score %.3f after %d turns",
                session_id, state.cumulative_score, state.turn_number,
            )
        elif (
            state.escalated
            and state.cumulative_score < self.block_threshold
            and len(state.risk_history) >= self.window_size
        ):
            # De-escalate once a full window of turns has passed with lower cumulative risk
            state.escalated = False
            logger.info(
                "Session %s DE-ESCALATED — cumulative score %.3f over last %d turns",
                session_id, state.cumulative_score, self.window_size,
            )

        return state

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def apply_escalation(self, composite_score: float, state: SessionState) -> float:
        """
        If the session has escalated, multiply the composite score by the
        escalation multiplier (capped at 1.0).
        """
        if state.escalated:
            return min(1.0, composite_score * self.escalation_multiplier)
        return composite_score

    @property
    def active_sessions(self) -> int:
        return len(self._sessions)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _evict_stale(self) -> None:
        now = time.time()
        stale = [
            sid for sid, s in self._sessions.items()
            if now - s.last_updated > SESSION_TTL_SECONDS
        ]
        for sid in stale:
            del self._sessions[sid]
        if stale:
            logger.debug("Evicted %d stale sessions", len(stale))


# ── Singleton ─────────────────────────────────────────────────────────────────
_aggregator: SessionAggregator | None = None


def get_session_aggregator() -> SessionAggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = SessionAggregator()
    return _aggregator
