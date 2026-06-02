# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""
Unit tests for Ansible output parsing utilities (Issue #9286).
"""

import pytest

from services.ansible_utils import _extract_failure_summary


class TestExtractFailureSummary:
    def test_regular_task_failure(self):
        """Regular task failures are attributed correctly."""
        output = """
TASK [backend : Backend | Check cognition_seed.yaml exists (#4679)] ****
fatal: [00-SLM-Manager]: FAILED! => {
  "msg": "File not found"
}
"""
        result = _extract_failure_summary(output)
        assert "00-SLM-Manager" in result
        assert "backend : Backend | Check cognition_seed.yaml exists (#4679)" in result
        assert "File not found" in result

    def test_handler_failure_attributed_to_handler(self):
        """Handler failures are attributed to the handler, not the last task (Issue #9286)."""
        output = """
TASK [backend : Backend | Check cognition_seed.yaml exists (#4679)] ****
ok: [00-SLM-Manager]

RUNNING HANDLER [backend : restart backend] *****
fatal: [00-SLM-Manager]: FAILED! => {
  "msg": "Unable to restart service autobot-backend: Job for autobot-backend.service failed because the control process exited with error code."
}
"""
        result = _extract_failure_summary(output)
        assert "00-SLM-Manager" in result
        assert "backend : restart backend" in result
        assert "backend : Backend | Check cognition_seed.yaml exists" not in result
        assert "Unable to restart service" in result

    def test_multiple_failures(self):
        """Multiple host failures are aggregated."""
        output = """
TASK [common : Update apt cache] ****
fatal: [node-01]: FAILED! => {
  "msg": "Failed to update apt cache"
}

RUNNING HANDLER [backend : restart backend] *****
fatal: [node-02]: FAILED! => {
  "msg": "Service restart failed"
}
"""
        result = _extract_failure_summary(output)
        assert "2 hosts failed" in result
        assert "node-01" in result
        assert "common : Update apt cache" in result
        assert "node-02" in result
        assert "backend : restart backend" in result

    def test_no_failures_returns_empty(self):
        """Empty string is returned when no failures are detected."""
        output = """
TASK [common : Update apt cache] ****
ok: [node-01]

PLAY RECAP *****
node-01                    : ok=5    changed=0    unreachable=0    failed=0
"""
        result = _extract_failure_summary(output)
        assert result == ""

    def test_unreachable_host(self):
        """UNREACHABLE failures are detected and labeled correctly."""
        output = """
TASK [common : Gather facts] ****
fatal: [node-01]: UNREACHABLE! => {
  "msg": "Failed to connect to the host via ssh"
}
"""
        result = _extract_failure_summary(output)
        assert "node-01" in result
        assert "unreachable" in result.lower()
        assert "Failed to connect" in result
