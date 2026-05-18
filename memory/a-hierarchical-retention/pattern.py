"""Hierarchical Retention pattern.

Reference implementation of the 4-layer memory hierarchy from column
lecture 03-02. The core observation: agent memory is not one thing.
Different facts have different scopes, lifetimes, and access frequencies,
and stuffing everything into one prompt either blows the token budget
or buries the signal.

Four layers, from coarsest to finest:

* **USER** — across all sessions, permanent (user profile, preferences)
* **PROJECT** — within one project, semi-permanent (tech stack, rules)
* **SESSION** — within one conversation, short-lived (task progress)
* **TURN** — within one tool round, ephemeral (just-fetched results)

The pattern's invariant: **inner layers override outer layers**. When the
USER layer says the user prefers OOP examples but the SESSION layer says
"this user just asked for a functional example today", the SESSION value
wins for this session, without overwriting the USER preference.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Layer(Enum):
    USER = "user"           # cross-session, permanent
    PROJECT = "project"     # within a project, semi-permanent
    SESSION = "session"     # within a conversation, short-lived
    TURN = "turn"           # within one tool round, ephemeral


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryLayer:
    """One layer in the hierarchy: schema + TTL + backend + token budget."""

    name: Layer
    backend: str                # "file" / "redis" / "postgres" / "vector" / "memory"
    ttl_seconds: int | None     # None means permanent
    token_budget: int           # cap on tokens this layer can contribute to a prompt
    content: dict[str, Any] = field(default_factory=dict)
    last_modified: str = field(default_factory=_now_iso)

    def is_expired(self, *, now: datetime | None = None) -> bool:
        if self.ttl_seconds is None:
            return False
        ref = now or datetime.now(timezone.utc)
        elapsed = (ref - datetime.fromisoformat(self.last_modified)).total_seconds()
        return elapsed > self.ttl_seconds


# Default 4-layer configuration. Real production tunes these per scenario.
DEFAULT_LAYERS: dict[Layer, dict[str, Any]] = {
    Layer.USER:    {"backend": "postgres", "ttl_seconds": None,   "token_budget": 2_000},
    Layer.PROJECT: {"backend": "file",     "ttl_seconds": None,   "token_budget": 4_000},
    Layer.SESSION: {"backend": "redis",    "ttl_seconds": 86_400, "token_budget": 8_000},
    Layer.TURN:    {"backend": "memory",   "ttl_seconds": 300,    "token_budget": 2_000},
}

# Read order: inner first → outer last. Inner overrides outer.
READ_ORDER = [Layer.TURN, Layer.SESSION, Layer.PROJECT, Layer.USER]
# Write/assemble order: outer first → inner last (build context coarse → fine).
ASSEMBLE_ORDER = [Layer.USER, Layer.PROJECT, Layer.SESSION, Layer.TURN]


class HierarchicalRetention:
    """Four-layer memory with override semantics."""

    def __init__(
        self,
        user_id: str,
        project_id: str,
        session_id: str,
        layer_config: dict[Layer, dict[str, Any]] | None = None,
    ) -> None:
        self.user_id = user_id
        self.project_id = project_id
        self.session_id = session_id
        cfg = layer_config or DEFAULT_LAYERS
        self.layers: dict[Layer, MemoryLayer] = {
            name: MemoryLayer(name=name, **cfg[name]) for name in cfg
        }

    # ──────────────── public ────────────────

    def write(self, layer: Layer, key: str, value: Any) -> None:
        """Write to a specific layer. Backend dispatch is the caller's job."""
        self.layers[layer].content[key] = value
        self.layers[layer].last_modified = _now_iso()

    def read(self, key: str) -> tuple[Any | None, Layer | None]:
        """Inner-first lookup. Returns (value, layer) or (None, None)."""
        for layer in READ_ORDER:
            holder = self.layers[layer]
            if holder.is_expired():
                continue
            if key in holder.content:
                return holder.content[key], layer
        return None, None

    def assemble_prompt_context(self) -> str:
        """Render coarse → fine. Skip expired or empty layers."""
        sections: list[str] = []
        for layer in ASSEMBLE_ORDER:
            holder = self.layers[layer]
            if holder.is_expired() or not holder.content:
                continue
            section = f"## {layer.value.upper()} CONTEXT\n"
            section += json.dumps(holder.content, ensure_ascii=False, indent=2)
            sections.append(section)
        return "\n\n".join(sections)

    def evict_expired(self) -> list[str]:
        """Clear expired layers. Returns names of layers actually cleared."""
        evicted: list[str] = []
        for name, holder in self.layers.items():
            if holder.is_expired():
                evicted.append(name.value)
                holder.content.clear()
                holder.last_modified = _now_iso()
        return evicted

    def health_report(self) -> dict[str, Any]:
        """Per-layer state — wire to a dashboard for production monitoring."""
        return {
            "user_id": self.user_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "layers": {
                layer.value: {
                    "items": len(self.layers[layer].content),
                    "expired": self.layers[layer].is_expired(),
                    "backend": self.layers[layer].backend,
                    "ttl_seconds": self.layers[layer].ttl_seconds,
                    "token_budget": self.layers[layer].token_budget,
                }
                for layer in Layer
            },
        }
