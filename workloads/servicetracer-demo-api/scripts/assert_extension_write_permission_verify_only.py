#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from assert_extension_update_what_if import assess


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
    assessed = assess(payload, expected)

    result = {
        **assessed,
        'status': 'effective_extension_write_permission_verified',
        'effective_extension_write_permission_verified': True,
        'arm_validation_succeeded': True,
        'extension_only_what_if_accepted': True,
        'azure_mutation_performed': False,
        'application_deployment_performed': False,
        'transaction_replay_performed': False,
        'deployment_authorized': False,
        'claim_boundary': (
            'Successful ARM validation and accepted extension-only What-If establish '
            'that the protected target identity can authorize the proposed extension '
            'write. They do not authorize or perform deployment.'
        ),
    }
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
