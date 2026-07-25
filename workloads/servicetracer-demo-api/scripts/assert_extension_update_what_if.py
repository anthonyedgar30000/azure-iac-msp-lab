#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalize(value: str) -> str:
    return value.rstrip('/').lower()


def assess(payload: dict, expected_resource_id: str) -> dict:
    status = payload.get('status')
    if status not in {None, 'Succeeded'}:
        raise ValueError(f'What-If status is not successful: {status!r}')

    changes = payload.get('changes')
    if not isinstance(changes, list):
        raise ValueError('What-If changes must be a list')

    material = [
        item for item in changes
        if str(item.get('changeType', '')).lower() not in {'nochange', 'ignore'}
    ]
    if len(material) != 1:
        raise ValueError(f'expected exactly one material change, observed {len(material)}')

    change = material[0]
    observed_id = str(change.get('resourceId') or '')
    change_type = str(change.get('changeType') or '')
    if normalize(observed_id) != normalize(expected_resource_id):
        raise ValueError(f'unexpected changed resource: {observed_id!r}')
    if change_type != 'Modify':
        raise ValueError(f'expected extension Modify, observed {change_type!r}')

    return {
        'status': 'accepted_extension_only_modify',
        'expected_resource_id': expected_resource_id,
        'observed_resource_id': observed_id,
        'change_type': change_type,
        'material_change_count': len(material),
        'deployment_authorized': True,
        'scope_escape_observed': False,
        'delete_or_replace_observed': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('what_if_json', type=Path)
    parser.add_argument('--subscription-id', required=True)
    parser.add_argument('--resource-group', required=True)
    parser.add_argument('--vm-name', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    expected = (
        f'/subscriptions/{args.subscription_id}'
        f'/resourceGroups/{args.resource_group}'
        f'/providers/Microsoft.Compute/virtualMachines/{args.vm_name}'
        '/extensions/servicetracer-demo-api'
    )
    payload = json.loads(args.what_if_json.read_text(encoding='utf-8'))
    result = assess(payload, expected)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
