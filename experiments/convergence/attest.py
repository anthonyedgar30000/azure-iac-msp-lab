#!/usr/bin/env python3
"""Shadow-mode dependency attestation and poison propagation."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

VALID = "VALID"
FAULTED = "FAULTED"
POISONED = "POISONED"
UNKNOWN = "UNKNOWN"

EDGE_STATES = {VALID, FAULTED, UNKNOWN}
NODE_OBSERVATION_STATES = {VALID, FAULTED, UNKNOWN}


def load_json_compatible_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _descendants(start: str, adjacency: dict[str, list[str]]) -> set[str]:
    seen: set[str] = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(adjacency.get(node, []))
    return seen


def _poison(
    affected: set[str],
    node_states: dict[str, str],
) -> None:
    """Mark only still-trusted dependent nodes as POISONED.

    A direct FAULTED or UNKNOWN local observation is more specific than
    downstream poison and is therefore preserved.
    """
    for node in affected:
        if node_states[node] == VALID:
            node_states[node] = POISONED


def evaluate(
    topology: dict[str, Any],
    edge_observations: dict[str, str],
    node_observations: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Evaluate local/node attestations and poison only dependent paths.

    Missing edge observations are UNKNOWN by design: no evidence means no
    trust propagation. Node observations are optional; when supplied, a
    direct node FAULTED or UNKNOWN result poisons only its descendants.

    This function is shadow-only and performs no remediation.
    """
    nodes = topology["nodes"]
    edges = topology["edges"]
    node_states = {node: VALID for node in nodes}
    edge_states: dict[str, str] = {}
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}

    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])

    failures: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []
    node_failures: list[dict[str, Any]] = []
    node_unknowns: list[dict[str, Any]] = []
    actions: list[dict[str, str]] = []

    for node, observed in (node_observations or {}).items():
        if node not in node_states:
            raise ValueError(f"unknown node observation target: {node}")
        if observed not in NODE_OBSERVATION_STATES:
            raise ValueError(f"invalid node state for {node}: {observed}")

        if observed == VALID:
            continue

        node_states[node] = observed
        affected = _descendants(node, adjacency) - {node}
        _poison(affected, node_states)
        record = {
            "node": node,
            "poisoned_path": sorted(affected),
        }
        if observed == FAULTED:
            node_failures.append(record)
        else:
            node_unknowns.append(record)

    for edge in edges:
        edge_id = edge["id"]
        observed = edge_observations.get(edge_id, UNKNOWN)
        if observed not in EDGE_STATES:
            raise ValueError(f"invalid state for {edge_id}: {observed}")

        edge_states[edge_id] = observed

        if observed == VALID:
            continue

        affected = _descendants(edge["to"], adjacency)
        _poison(affected, node_states)

        record = {
            "edge": edge_id,
            "attestor": edge["attestor"],
            "from": edge["from"],
            "to": edge["to"],
            "poisoned_path": sorted(affected),
        }

        if observed == FAULTED:
            failures.append(record)
            action = edge.get("golden_action")
            if action:
                actions.append({"edge": edge_id, "action": action})
        else:
            unknowns.append(record)

    return {
        "edge_states": edge_states,
        "node_states": node_states,
        "failures": failures,
        "unknowns": unknowns,
        "node_failures": node_failures,
        "node_unknowns": node_unknowns,
        "candidate_actions": actions,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("topology")
    parser.add_argument("scenario")
    args = parser.parse_args()

    topology = load_json_compatible_yaml(args.topology)
    scenario = load_json_compatible_yaml(args.scenario)
    result = evaluate(
        topology,
        scenario["edge_observations"],
        scenario.get("node_observations", {}),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
