"""agent-config Python harness.

Installer / cleaner / verifier for Claude Code + Codex CLI templates.
Replaces the legacy bash scripts (install.sh, clean.sh, verify-install.sh)
with a cross-platform, testable, security-hardened implementation.
"""

__all__ = ["fs", "install", "clean", "verify_install", "merge_settings", "paths"]
