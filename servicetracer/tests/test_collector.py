from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from servicetracer.collector import (
    JsonlSpool,
    build_http_server,
    extract_structured_syslog_record,
    load_collector_records,
)


SAMPLE_RECORD = {
    "source_type": "vpn_syslog",
    "event_id": "COLLECTOR-001",
    "timestamp": "2026-07-19T14:00:00Z",
    "device": "VPN-01",
    "session_id": "ATT-001",
    "event": "tls_completed",
    "elapsed_ms": 310,
}


class JsonlSpoolTests(unittest.TestCase):
    def test_persists_records_and_counts_idempotent_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "evidence.jsonl"
            spool = JsonlSpool(path)

            first = spool.append([SAMPLE_RECORD])
            duplicate = spool.append([json.loads(json.dumps(SAMPLE_RECORD))])

            self.assertEqual(first.records_accepted, 1)
            self.assertEqual(duplicate.records_accepted, 0)
            self.assertEqual(duplicate.idempotent_duplicates, 1)
            self.assertEqual(spool.status()["records"], 1)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")), SAMPLE_RECORD
            )

    def test_rejects_divergent_reused_evidence_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            spool = JsonlSpool(Path(temp_dir) / "evidence.jsonl")
            spool.append([SAMPLE_RECORD])
            changed = {**SAMPLE_RECORD, "elapsed_ms": 999}
            with self.assertRaisesRegex(ValueError, "reused with different content"):
                spool.append([changed])

    def test_batch_is_preflighted_before_any_records_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "evidence.jsonl"
            spool = JsonlSpool(path)
            valid = {**SAMPLE_RECORD, "event_id": "COLLECTOR-002"}
            conflicting = {**valid, "elapsed_ms": 999}

            with self.assertRaisesRegex(ValueError, "reused with different content"):
                spool.append([valid, conflicting])

            self.assertEqual(path.read_text(encoding="utf-8"), "")

    def test_loads_json_object_array_and_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            object_path = root / "record.json"
            array_path = root / "records.json"
            jsonl_path = root / "records.jsonl"
            object_path.write_text(json.dumps(SAMPLE_RECORD), encoding="utf-8")
            array_path.write_text(
                json.dumps([{**SAMPLE_RECORD, "event_id": "COLLECTOR-002"}]),
                encoding="utf-8",
            )
            jsonl_path.write_text(
                json.dumps({**SAMPLE_RECORD, "event_id": "COLLECTOR-003"}) + "\n",
                encoding="utf-8",
            )

            records = load_collector_records([object_path, array_path, jsonl_path])
            self.assertEqual([record["event_id"] for record in records], [
                "COLLECTOR-001",
                "COLLECTOR-002",
                "COLLECTOR-003",
            ])


class StructuredSyslogTests(unittest.TestCase):
    def test_extracts_json_after_marker_without_interpreting_vendor_prefix(self) -> None:
        message = (
            "<134>1 2026-07-19T14:00:00Z vpn-01 vendor - - - "
            "@servicetracer " + json.dumps(SAMPLE_RECORD)
        )
        self.assertEqual(extract_structured_syslog_record(message), SAMPLE_RECORD)

    def test_rejects_unstructured_vendor_message(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not contain"):
            extract_structured_syslog_record("VPN tunnel changed state")


class HTTPCollectorTests(unittest.TestCase):
    def test_authenticated_http_ingestion_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            spool = JsonlSpool(Path(temp_dir) / "evidence.jsonl")
            server = build_http_server(
                spool,
                "127.0.0.1",
                0,
                bearer_token="test-secret",
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            body = json.dumps(SAMPLE_RECORD).encode("utf-8")

            unauthorized = Request(
                f"{base_url}/v1/records",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as context:
                urlopen(unauthorized, timeout=5)
            self.assertEqual(context.exception.code, 401)

            authorized = Request(
                f"{base_url}/v1/records",
                data=body,
                headers={
                    "Authorization": "Bearer test-secret",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urlopen(authorized, timeout=5) as response:
                receipt = json.load(response)
            self.assertEqual(response.status, 202)
            self.assertEqual(receipt["records_accepted"], 1)

            status_request = Request(
                f"{base_url}/v1/status",
                headers={"Authorization": "Bearer test-secret"},
            )
            with urlopen(status_request, timeout=5) as response:
                status = json.load(response)
            self.assertEqual(status["records"], 1)

            with urlopen(f"{base_url}/healthz", timeout=5) as response:
                health = json.load(response)
            self.assertEqual(health["status"], "ok")

            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
