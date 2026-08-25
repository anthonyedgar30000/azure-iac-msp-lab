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


def evaluate(topology: dict[str, Any], edge_observations: dict[str, str]) -> dict[str, Any]:
    """Evaluate local edge attestations and poison only dependent paths.

    Missing observations are UNKNOWN by design: no evidence means no trust
    propagation. This function is shadow-only and performs no remediation.
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
    actions: list[dict[str, str]] = []

    for edge in edges:
        edge_id = edge["id"]
        observed = edge_observations.get(edge_id, UNKNOWN)
        if observed not in EDGE_STATES:
            raise ValueError(f"invalid state for {edge_id}: {observed}")

        edge_states[edge_id] = observed

        if observed == VALID:
            continue

        affected = _descendants(edge["to"], adjacency)
        for node in affected:
            node_states[node] = POISONED

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
    result = evaluate(topology, scenario["edge_observations"])
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
