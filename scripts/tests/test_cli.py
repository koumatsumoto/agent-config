"""Tests for scripts/cli.py (install / clean / verify / merge + fs helpers).

Run with the scripts/ dir as the top-level import root:
    python3 -m unittest discover -s scripts/tests -t scripts
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cli

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


def _verified_spec() -> cli.FileSpec:
    """A TEMPLATE_FILES spec that clean()/verify() manage.

    Every template file is a full-template copy, so any spec works for tests
    asserting removal / drift detection; the first one is representative.
    """
    return cli.TEMPLATE_FILES[0]


def _global_guideline_specs() -> list[cli.FileSpec]:
    """The shared agent guidelines refreshed from the template on every install."""
    dests = {".claude/CLAUDE.md", ".codex/AGENTS.md"}
    return [s for s in cli.TEMPLATE_FILES if s.dest_rel in dests]


def _skill_docs() -> list[Path]:
    """Every markdown file in the managed skills tree, skill-root relative.

    Skills are deployed as whole trees, so adding or restructuring reference
    files must reach every skills root without touching the manifest.
    """
    skills_root = cli.REPO_ROOT / "templates" / "skills"
    return [p.relative_to(skills_root) for p in sorted(skills_root.rglob("*.md"))]


def _codex_profile_specs() -> list[cli.FileSpec]:
    """Codex profile files loaded by `codex --profile <name>`."""
    return [s for s in cli.TEMPLATE_FILES if s.dest_rel.startswith(".codex/") and s.dest_rel.endswith(".config.toml")]


# --------------------------------------------------------------------------- #
# fs helpers
# --------------------------------------------------------------------------- #
class AtomicWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_atomic_write_creates_file(self) -> None:
        target = self.dir / "out.txt"
        cli.atomic_write_text(target, "hello")
        self.assertEqual(target.read_text(encoding="utf-8"), "hello")

    def test_atomic_write_applies_0600_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        target = self.dir / "secret.txt"
        cli.atomic_write_text(target, "secret")
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_atomic_write_replaces_existing(self) -> None:
        target = self.dir / "out.txt"
        target.write_text("old", encoding="utf-8")
        cli.atomic_write_text(target, "new")
        self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_atomic_write_replaces_symlink_at_dest(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        outside = self.dir / "outside.txt"
        outside.write_text("outside-original", encoding="utf-8")
        target = self.dir / "linked.txt"
        os.symlink(outside, target)
        cli.atomic_write_text(target, "new-content")
        # The symlink at `target` is replaced by a regular file; outside is unchanged.
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), "new-content")
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside-original")

    def test_atomic_write_no_predictable_tmp_left_behind(self) -> None:
        target = self.dir / "out.txt"
        cli.atomic_write_text(target, "x")
        leftovers = [p for p in self.dir.iterdir() if p.name.startswith("out.txt.")]
        self.assertEqual(leftovers, [])


class IsWithinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_inside_directory(self) -> None:
        self.assertTrue(cli.is_within(self.dir / "a" / "b", self.dir))

    def test_outside_directory(self) -> None:
        outside = Path(tempfile.gettempdir()) / "definitely-not-here-12345"
        self.assertFalse(cli.is_within(outside, self.dir))

    def test_assert_within_raises(self) -> None:
        outside = Path(tempfile.gettempdir()) / "definitely-not-here-12345"
        with self.assertRaises(PermissionError):
            cli.assert_within(outside, self.dir)


class EnsureFileModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))
        if not cli.is_posix():
            self.skipTest("POSIX-only")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def _run(self, path: Path, mode: int) -> tuple[bool, str]:
        with patch("sys.stdout", new=StringIO()) as out:
            changed = cli.ensure_file_mode(path, mode)
        return changed, out.getvalue()

    def test_restores_a_widened_mode_and_reports_it(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("x", encoding="utf-8")
        target.chmod(0o644)
        changed, out = self._run(target, cli.FILE_MODE)
        self.assertTrue(changed)
        self.assertEqual(target.stat().st_mode & 0o777, cli.FILE_MODE)
        self.assertIn("mode:", out)
        self.assertIn("0o644", out)

    def test_silent_when_the_mode_already_matches(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("x", encoding="utf-8")
        target.chmod(cli.FILE_MODE)
        changed, out = self._run(target, cli.FILE_MODE)
        self.assertFalse(changed)
        self.assertEqual(out, "")

    def test_never_changes_the_mode_through_a_symlink(self) -> None:
        # chmod follows the link, so this would change the mode of a file the
        # installer does not manage — including one outside its boundary.
        outside = self.dir / "outside.txt"
        outside.write_text("x", encoding="utf-8")
        outside.chmod(0o644)
        link = self.dir / "link.txt"
        link.symlink_to(outside)
        changed, out = self._run(link, cli.FILE_MODE)
        self.assertFalse(changed)
        self.assertEqual(out, "")
        self.assertEqual(outside.stat().st_mode & 0o777, 0o644)

    def test_missing_path_is_a_no_op(self) -> None:
        changed, _ = self._run(self.dir / "absent.txt", cli.FILE_MODE)
        self.assertFalse(changed)


class InstallFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))
        self.src = self.dir / "src.txt"
        self.dest = self.dir / "out" / "dest.txt"
        self.src.write_text("hello", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_copies_when_missing(self) -> None:
        status = cli.install_file(self.src, self.dest)
        self.assertEqual(status, "copied")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "hello")

    def test_ok_when_identical(self) -> None:
        cli.install_file(self.src, self.dest)
        status = cli.install_file(self.src, self.dest)
        self.assertEqual(status, "ok")

    def test_ok_still_restores_a_widened_mode(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        cli.install_file(self.src, self.dest)
        self.dest.chmod(0o644)
        with patch("sys.stdout", new=StringIO()):
            status = cli.install_file(self.src, self.dest)
        self.assertEqual(status, "ok", "content is unchanged, so no rewrite")
        self.assertEqual(self.dest.stat().st_mode & 0o777, cli.FILE_MODE)
        self.assertFalse(self.dest.with_name(self.dest.name + ".bak").exists())


    def test_replaces_when_different_with_backup(self) -> None:
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        self.dest.write_text("old", encoding="utf-8")
        status = cli.install_file(self.src, self.dest)
        self.assertEqual(status, "replaced")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "hello")
        bak = self.dest.with_name(self.dest.name + ".bak")
        self.assertEqual(bak.read_text(encoding="utf-8"), "old")

    def test_refuses_symlink_source(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        link = self.dir / "link.txt"
        os.symlink(self.src, link)
        with self.assertRaises(FileNotFoundError):
            cli.install_file(link, self.dest)


class InstallTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))
        self.src_root = self.dir / "src"
        self.dest_root = self.dir / "dest"
        (self.src_root / "sub").mkdir(parents=True)
        (self.src_root / "a.txt").write_text("a", encoding="utf-8")
        (self.src_root / "sub" / "b.txt").write_text("b", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_copies_tree(self) -> None:
        results = cli.install_tree(self.src_root, self.dest_root)
        statuses = sorted(s for s, _ in results)
        self.assertEqual(statuses, ["copied", "copied"])
        self.assertEqual((self.dest_root / "a.txt").read_text(encoding="utf-8"), "a")
        self.assertEqual((self.dest_root / "sub" / "b.txt").read_text(encoding="utf-8"), "b")

    def test_boundary_enforcement(self) -> None:
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, self.dest_root, boundary=self.dir / "other")

    def test_idempotent_rerun(self) -> None:
        cli.install_tree(self.src_root, self.dest_root)
        results = cli.install_tree(self.src_root, self.dest_root)
        statuses = sorted(s for s, _ in results)
        self.assertEqual(statuses, ["ok", "ok"])

    def test_refuses_symlink_in_template(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        target = self.src_root / "a.txt"
        link = self.src_root / "link.txt"
        os.symlink(target, link)
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, self.dest_root)

    def test_refuses_symlink_loop_in_template(self) -> None:
        # A symlink loop inside src_root would hang Python 3.13's rglob
        # if it followed symlinks; install_tree must use a non-following walk.
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        loop = self.src_root / "loop"
        os.symlink(self.src_root.resolve(), loop)
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, self.dest_root)

    def test_boundary_checked_before_dest_root_mkdir(self) -> None:
        # Defense-in-depth: install_tree must refuse a dest_root outside the
        # boundary BEFORE creating or chmod'ing it.
        unwritten = self.dir / "outside"
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, unwritten, boundary=self.dir / "other")
        self.assertFalse(unwritten.exists())


class PruneTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="prune-test-"))
        self.src_root = self.dir / "src"
        self.dest_root = self.dir / "dest"
        # source ships skillA with one file and one nested file
        (self.src_root / "skillA" / "sub").mkdir(parents=True)
        (self.src_root / "skillA" / "keep.txt").write_text("k", encoding="utf-8")
        (self.src_root / "skillA" / "sub" / "deep.txt").write_text("d", encoding="utf-8")
        # dest starts as an exact copy of src (a clean managed deployment)
        (self.dest_root / "skillA" / "sub").mkdir(parents=True)
        (self.dest_root / "skillA" / "keep.txt").write_text("k", encoding="utf-8")
        (self.dest_root / "skillA" / "sub" / "deep.txt").write_text("d", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def _prune(self) -> list[Path]:
        return cli.prune_tree(self.src_root, self.dest_root, boundary=self.dir)

    def test_no_orphans_returns_empty(self) -> None:
        self.assertEqual(self._prune(), [])

    def test_prunes_orphan_file_in_managed_dir(self) -> None:
        orphan = self.dest_root / "skillA" / "qa.md"
        orphan.write_text("stale", encoding="utf-8")
        pruned = self._prune()
        self.assertEqual(pruned, [orphan])
        self.assertFalse(orphan.exists())
        self.assertTrue(orphan.with_name("qa.md.bak").exists())
        self.assertTrue((self.dest_root / "skillA" / "keep.txt").exists())

    def test_prunes_orphan_subdir_in_managed_dir(self) -> None:
        gone = self.dest_root / "skillA" / "gone"
        gone.mkdir()
        (gone / "x.txt").write_text("x", encoding="utf-8")
        pruned = self._prune()
        self.assertEqual(pruned, [gone])
        self.assertFalse(gone.exists())
        self.assertTrue(gone.with_name("gone.bak").is_dir())

    def test_preserves_user_added_toplevel_dir(self) -> None:
        user = self.dest_root / "my-custom"
        user.mkdir()
        (user / "SKILL.md").write_text("mine", encoding="utf-8")
        self.assertEqual(self._prune(), [])
        self.assertTrue((user / "SKILL.md").exists())

    def test_preserves_user_added_toplevel_file(self) -> None:
        loose = self.dest_root / "user-note.md"
        loose.write_text("mine", encoding="utf-8")
        self.assertEqual(self._prune(), [])
        self.assertTrue(loose.exists())

    def test_prunes_orphan_symlink_without_following(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        target = self.src_root / "skillA" / "keep.txt"  # in-boundary target
        link = self.dest_root / "skillA" / "orphan-link.txt"  # no src counterpart
        os.symlink(target, link)
        pruned = self._prune()
        self.assertEqual(pruned, [link])
        self.assertFalse(link.exists() or link.is_symlink())
        bak = link.with_name("orphan-link.txt.bak")
        self.assertTrue(bak.is_symlink())  # the symlink itself was moved, not followed
        self.assertTrue(target.exists())  # target untouched

    def test_skips_bak_entries(self) -> None:
        bak = self.dest_root / "skillA" / "keep.txt.bak"
        bak.write_text("old", encoding="utf-8")
        self.assertEqual(self._prune(), [])
        self.assertTrue(bak.exists())

    def test_missing_dest_root_returns_empty(self) -> None:
        self.assertEqual(
            cli.prune_tree(self.src_root, self.dir / "nope", boundary=self.dir), []
        )

    def test_boundary_enforced(self) -> None:
        (self.dest_root / "skillA" / "orphan.txt").write_text("o", encoding="utf-8")
        with self.assertRaises(PermissionError):
            cli.prune_tree(self.src_root, self.dest_root, boundary=self.dir / "other")


class DecommissionedSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="decom-test-"))
        self.layout = cli.home_layout(self.home)
        self.skills = self.home / ".claude" / "skills"
        self.skills.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_deletes_decommissioned_skill_and_backup(self) -> None:
        name = cli.DECOMMISSIONED_SKILLS[0]
        old = self.skills / name
        old.mkdir()
        (old / "SKILL.md").write_text("old", encoding="utf-8")
        backup = self.skills / f"{name}.bak"
        backup.mkdir()
        (backup / "SKILL.md").write_text("backup", encoding="utf-8")
        archive = self.skills.parent / "retired-skills"
        (archive / name).mkdir(parents=True)
        (archive / name / "SKILL.md").write_text("archive", encoding="utf-8")
        removed = cli.remove_decommissioned_skills(self.layout)
        self.assertEqual(removed, [old, backup, archive])
        self.assertFalse(old.exists())
        self.assertFalse(backup.exists())
        self.assertFalse(archive.exists())

    def test_preserves_user_added_and_current_skills(self) -> None:
        keep = self.skills / "my-skill"
        keep.mkdir()
        (keep / "SKILL.md").write_text("mine", encoding="utf-8")
        self.assertEqual(cli.remove_decommissioned_skills(self.layout), [])
        self.assertTrue((keep / "SKILL.md").exists())

    def test_removes_from_every_skills_root(self) -> None:
        name = cli.DECOMMISSIONED_SKILLS[0]
        agents = self.home / ".agents" / "skills"
        agents.mkdir(parents=True)
        (self.skills / name).mkdir()
        (agents / name).mkdir()
        removed = cli.remove_decommissioned_skills(self.layout)
        self.assertEqual(
            sorted(removed), sorted([self.skills / name, agents / name])
        )

    @unittest.skipUnless(cli.is_posix(), "symlink behavior is POSIX-only")
    def test_unlinks_obsolete_symlinks_without_following_them(self) -> None:
        name = cli.DECOMMISSIONED_SKILLS[0]
        outside = self.home / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep", encoding="utf-8")
        os.symlink(outside, self.skills / name)
        os.symlink(outside, self.skills.parent / "retired-skills")

        cli.remove_decommissioned_skills(self.layout)

        self.assertFalse((self.skills / name).exists())
        self.assertFalse((self.skills.parent / "retired-skills").exists())
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "keep")


class DecommissionedFilesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="decom-test-"))
        self.layout = cli.home_layout(self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_retires_decommissioned_config_to_backup(self) -> None:
        rel = cli.DECOMMISSIONED_FILES[0]
        target = self.home / rel
        target.parent.mkdir(parents=True)
        target.write_text("stale", encoding="utf-8")
        removed = cli.remove_decommissioned_files(self.layout)
        self.assertEqual(removed, [target])
        self.assertFalse(target.exists())
        self.assertEqual(target.with_name(target.name + ".bak").read_text(encoding="utf-8"), "stale")

    def test_skips_absent_paths(self) -> None:
        self.assertEqual(cli.remove_decommissioned_files(self.layout), [])


class SkillMetadataTests(unittest.TestCase):
    def test_names_use_standard_format_and_match_directory(self) -> None:
        skills_root = cli.REPO_ROOT / "templates" / "skills"
        skill_files = sorted(skills_root.glob("*/SKILL.md"))
        self.assertTrue(skill_files, "no managed skills found")

        for skill_file in skill_files:
            name_line = next(
                (
                    line
                    for line in skill_file.read_text(encoding="utf-8").splitlines()
                    if line.startswith("name: ")
                ),
                None,
            )
            self.assertIsNotNone(name_line, f"missing name: {skill_file}")
            name = name_line.removeprefix("name: ")
            self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertTrue(name.startswith("km-"), f"missing km- prefix: {name}")
            self.assertEqual(skill_file.parent.name, name)

    def test_verification_material_stays_out_of_the_distributed_tree(self) -> None:
        """scenario bank は配布されない。

        bank は repo のメンテナが改善を検証するための材料で、runtime では
        読まれない。`templates/skills` 配下に置くと 3 つの skills ツリーへ
        そのまま配られ、配布先で stale copy になる。
        """
        skills_root = cli.REPO_ROOT / "templates" / "skills"
        strays = sorted(
            str(path.relative_to(cli.REPO_ROOT))
            for path in skills_root.rglob("evals")
            if path.is_dir()
        )
        self.assertEqual(strays, [])

    def test_internal_reference_paths_resolve(self) -> None:
        """A skill's cross-file loads must point at files that exist.

        Skills hand reference files to the agent by path, so a dangling path
        silently drops whatever rules that file was carrying — invisible in a
        diff and invisible at runtime.
        """
        skills_root = cli.REPO_ROOT / "templates" / "skills"
        # Backticked, skill-root-relative markdown paths: the form skills use to
        # name a reference file. `<role>`-style placeholders stand for a set and
        # are covered by the concrete siblings that resolve.
        pattern = re.compile(r"`((?:references|reference|reviewers|agents)/[^`]+\.md)`")
        dangling: list[str] = []
        for doc in sorted(skills_root.rglob("*.md")):
            skill_dir = skills_root / doc.relative_to(skills_root).parts[0]
            for rel in pattern.findall(doc.read_text(encoding="utf-8")):
                if "<" in rel:
                    continue
                if not (skill_dir / rel).is_file():
                    dangling.append(f"{doc.relative_to(cli.REPO_ROOT)} -> {rel}")
        self.assertEqual(dangling, [])

    def test_colon_tokens_are_stable_protocol_markers_only(self) -> None:
        repo_root = cli.REPO_ROOT
        source_files = [repo_root / "README.md", repo_root / "CLAUDE.md"]
        for root_name in ("scripts", "templates"):
            source_files.extend(
                path
                for path in (repo_root / root_name).rglob("*")
                if path.is_file()
                and path.suffix in {".css", ".html", ".js", ".md", ".py", ".sh"}
            )

        tokens: set[str] = set()
        for path in source_files:
            tokens.update(
                re.findall(r"km:[a-z][a-z0-9:-]*", path.read_text(encoding="utf-8"))
            )

        self.assertEqual(tokens, {"km:plan:managed", "km:review:report:complete"})


class BackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_backup_returns_none_when_missing(self) -> None:
        result = cli.backup(self.dir / "nope")
        self.assertIsNone(result)

    def test_backup_moves_file(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("v1", encoding="utf-8")
        result = cli.backup(target)
        self.assertEqual(result, target.with_name("f.txt.bak"))
        self.assertFalse(target.exists())
        self.assertEqual(result.read_text(encoding="utf-8"), "v1")

    def test_backup_replaces_existing_bak(self) -> None:
        target = self.dir / "f.txt"
        bak = target.with_name("f.txt.bak")
        target.write_text("v2", encoding="utf-8")
        bak.write_text("old-bak", encoding="utf-8")
        cli.backup(target)
        self.assertEqual(bak.read_text(encoding="utf-8"), "v2")

    def test_remove_with_backup_skipped_when_missing(self) -> None:
        self.assertEqual(cli.remove_with_backup(self.dir / "nope"), "skipped")

    def test_remove_with_backup_moves_to_bak(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("data", encoding="utf-8")
        result = cli.remove_with_backup(target)
        self.assertEqual(result, "backed_up")
        self.assertFalse(target.exists())
        self.assertEqual(target.with_name("f.txt.bak").read_text(encoding="utf-8"), "data")


# --------------------------------------------------------------------------- #
# settings.json: per-platform status-line command
# --------------------------------------------------------------------------- #
class StatuslineCommandTests(unittest.TestCase):
    HOME = Path("/home/user")
    WINDOWS_HOME = Path("C:/Users/user")

    def test_posix_uses_tilde_path(self) -> None:
        cmd = cli.statusline_command(
            self.HOME / ".claude/statusline.py",
            posix=True,
            python="/usr/bin/python3",
            home=self.HOME,
        )
        self.assertEqual(cmd, "~/.claude/statusline.py")

    def test_posix_uses_absolute_path_outside_home(self) -> None:
        # A configuration directory may live anywhere; `~` cannot address it.
        cmd = cli.statusline_command(
            Path("/opt/profiles/sub/statusline.py"),
            posix=True,
            python="/usr/bin/python3",
            home=self.HOME,
        )
        self.assertEqual(cmd, "/opt/profiles/sub/statusline.py")

    def test_windows_invokes_interpreter_with_absolute_path(self) -> None:
        cmd = cli.statusline_command(
            self.WINDOWS_HOME / ".claude/statusline.py",
            posix=False,
            python="C:/Python313/python.exe",
            home=self.WINDOWS_HOME,
        )
        self.assertEqual(
            cmd, '"C:/Python313/python.exe" "C:/Users/user/.claude/statusline.py"'
        )

    def test_windows_quotes_tolerate_spaces(self) -> None:
        home = Path("C:/Users/First Last")
        cmd = cli.statusline_command(
            home / ".claude/statusline.py",
            posix=False,
            python="C:/Program Files/Python/python.exe",
            home=home,
        )
        self.assertEqual(
            cmd,
            '"C:/Program Files/Python/python.exe" '
            '"C:/Users/First Last/.claude/statusline.py"',
        )

    def test_apply_rewrites_known_sections_only(self) -> None:
        template: dict[str, object] = {
            "statusLine": {"type": "command", "command": "~/.claude/statusline.py"},
            "subagentStatusLine": {"command": "~/.claude/subagent-statusline.py"},
            "language": "日本語",
        }
        out = cli.apply_statusline_commands(
            template,
            cli.home_layout(self.WINDOWS_HOME),
            posix=False,
            python="C:/py.exe",
        )
        self.assertEqual(
            out["statusLine"],
            {"type": "command", "command": '"C:/py.exe" "C:/Users/user/.claude/statusline.py"'},
        )
        self.assertEqual(
            out["subagentStatusLine"],
            {"command": '"C:/py.exe" "C:/Users/user/.claude/subagent-statusline.py"'},
        )
        # Unrelated keys are untouched.
        self.assertEqual(out["language"], "日本語")

    def test_apply_does_not_mutate_input(self) -> None:
        template: dict[str, object] = {
            "statusLine": {"command": "~/.claude/statusline.py"},
        }
        cli.apply_statusline_commands(
            template,
            cli.home_layout(self.WINDOWS_HOME),
            posix=False,
            python="C:/py.exe",
        )
        self.assertEqual(template["statusLine"], {"command": "~/.claude/statusline.py"})

    def test_apply_is_noop_on_posix(self) -> None:
        template: dict[str, object] = {
            "statusLine": {"command": "~/.claude/statusline.py"},
        }
        out = cli.apply_statusline_commands(
            template, cli.home_layout(self.HOME), posix=True, python="/usr/bin/python3"
        )
        self.assertEqual(out["statusLine"], {"command": "~/.claude/statusline.py"})

    def test_apply_points_at_the_claude_dir_on_posix(self) -> None:
        template: dict[str, object] = {
            "statusLine": {"command": "~/.claude/statusline.py"},
            "subagentStatusLine": {"command": "~/.claude/subagent-statusline.py"},
        }
        layout = cli.claude_dir_layout(self.HOME / ".claude-sub", self.HOME)
        out = cli.apply_statusline_commands(
            template, layout, posix=True, python="/usr/bin/python3"
        )
        self.assertEqual(out["statusLine"], {"command": "~/.claude-sub/statusline.py"})
        self.assertEqual(
            out["subagentStatusLine"],
            {"command": "~/.claude-sub/subagent-statusline.py"},
        )

    def test_apply_skips_section_without_command(self) -> None:
        template: dict[str, object] = {"statusLine": {"type": "command"}}
        out = cli.apply_statusline_commands(
            template,
            cli.home_layout(self.WINDOWS_HOME),
            posix=False,
            python="C:/py.exe",
        )
        self.assertEqual(out["statusLine"], {"type": "command"})


# --------------------------------------------------------------------------- #
# settings.json merge
# --------------------------------------------------------------------------- #
class MergeFunctionTests(unittest.TestCase):
    def test_template_wins_for_shared_keys(self) -> None:
        merged = cli.merge({"a": 1, "b": "tpl"}, {"a": 99})
        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"], "tpl")

    def test_template_keys_added(self) -> None:
        merged = cli.merge({"a": 1}, {})
        self.assertEqual(merged, {"a": 1})

    def test_user_only_keys_kept(self) -> None:
        merged = cli.merge({"a": 1}, {"theme": "dark"})
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["a"], 1)


class MergeIntoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="merge-test-"))
        self.template = self.dir / "template.json"
        self.dest = self.dir / "dest.json"
        self.bak = Path(f"{self.dest}.bak")
        self.template.write_text(json.dumps({"a": 1, "b": "template"}), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_creates_when_dest_missing(self) -> None:
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "created")
        self.assertEqual(json.loads(self.dest.read_text(encoding="utf-8")), {"a": 1, "b": "template"})

    def test_ok_when_no_change(self) -> None:
        cli.merge_into(self.template, self.dest)
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "ok")
        self.assertFalse(self.bak.exists())

    def test_merged_template_wins_user_only_kept(self) -> None:
        self.dest.write_text(json.dumps({"a": 99, "theme": "dark"}), encoding="utf-8")
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        merged = json.loads(self.dest.read_text(encoding="utf-8"))
        # template declares "a" -> template value wins (propagates on re-run)
        self.assertEqual(merged["a"], 1)
        # template does not declare "theme" -> user value is preserved
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["b"], "template")
        self.assertTrue(self.bak.exists())

    def test_invalid_json_warned_and_replaced(self) -> None:
        self.dest.write_text("{not valid", encoding="utf-8")
        with patch("sys.stderr", new=StringIO()) as err:
            result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertIn("warn:", err.getvalue())
        self.assertEqual(self.bak.read_text(encoding="utf-8"), "{not valid")

    def test_non_object_json_warned(self) -> None:
        self.dest.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with patch("sys.stderr", new=StringIO()) as err:
            result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertIn("warn:", err.getvalue())

    def test_template_must_be_object(self) -> None:
        self.template.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with self.assertRaises(ValueError):
            cli.merge_into(self.template, self.dest)

    def test_empty_dest_merges_template(self) -> None:
        # Exercises the `text.strip()` empty branch of read_existing.
        self.dest.write_text("", encoding="utf-8")
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertEqual(
            json.loads(self.dest.read_text(encoding="utf-8")),
            {"a": 1, "b": "template"},
        )

    def test_applies_0600_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        cli.merge_into(self.template, self.dest)
        mode = self.dest.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_transform_rewrites_template_before_merge(self) -> None:
        result = cli.merge_into(
            self.template, self.dest, transform=lambda t: {**t, "b": "transformed"}
        )
        self.assertEqual(result, "created")
        merged = json.loads(self.dest.read_text(encoding="utf-8"))
        self.assertEqual(merged["b"], "transformed")


class MergeCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="merge-test-"))
        self.template = self.dir / "template.json"
        self.dest = self.dir / "dest.json"
        self.template.write_text(json.dumps({"a": 1}), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_no_command_returns_usage_error(self) -> None:
        with patch("sys.stderr", new=StringIO()) as err:
            rc = cli.main(["cli.py"])
        self.assertEqual(rc, 2)
        self.assertIn("usage:", err.getvalue())

    def test_merge_missing_args_returns_2(self) -> None:
        with patch("sys.stderr", new=StringIO()) as err:
            rc = cli.main(["cli.py", "merge"])
        self.assertEqual(rc, 2)
        self.assertIn("usage:", err.getvalue())

    def test_unknown_command_returns_2(self) -> None:
        with patch("sys.stderr", new=StringIO()) as err:
            rc = cli.main(["cli.py", "bogus"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown command", err.getvalue())

    def test_merge_creates(self) -> None:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        self.assertEqual(rc, 0)
        self.assertIn("created:", out.getvalue())

    def test_merge_existing_emits_backup_and_merged(self) -> None:
        self.dest.write_text(json.dumps({"a": 99}), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        self.assertEqual(rc, 0)
        output = out.getvalue()
        self.assertIn("backup:", output)
        self.assertIn("merged:", output)

    def test_merge_noop_emits_ok(self) -> None:
        with patch("sys.stdout", new=StringIO()):
            cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        self.assertEqual(rc, 0)
        self.assertIn("ok:", out.getvalue())


# --------------------------------------------------------------------------- #
# install
# --------------------------------------------------------------------------- #
class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="install-test-"))
        self.layout = cli.home_layout(self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _run_install(self) -> str:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.install(self.layout)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_creates_all_template_files(self) -> None:
        self._run_install()
        for spec in cli.TEMPLATE_FILES:
            dest = self.home / spec.dest_rel
            self.assertTrue(dest.is_file(), f"missing: {dest}")

    def test_creates_managed_dirs(self) -> None:
        self._run_install()
        for sub in cli.INSTALL_HOME_DIRS:
            self.assertTrue((self.home / sub).is_dir())

    def test_every_skill_doc_reaches_each_skills_root(self) -> None:
        self._run_install()
        docs = _skill_docs()
        self.assertTrue(docs, "no managed skill docs found")
        for root_rel in (".claude/skills", ".agents/skills"):
            for rel in docs:
                self.assertTrue((self.home / root_rel / rel).is_file(), f"missing: {root_rel}/{rel}")

    def test_creates_settings_json(self) -> None:
        self._run_install()
        settings = self.home / cli.SETTINGS_DEST_REL
        self.assertTrue(settings.is_file())
        data = json.loads(settings.read_text(encoding="utf-8"))
        # statusLine is a known recommended key in the template
        self.assertIn("statusLine", data)

    def test_settings_statusline_command_runnable_on_platform(self) -> None:
        self._run_install()
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        command = data["statusLine"]["command"]
        if cli.is_posix():
            # POSIX keeps the tilde path so the shebang re-resolves the interpreter.
            self.assertEqual(command, "~/.claude/statusline.py")
        else:
            # Windows cannot run a bare .py: the interpreter must be named, and
            # the absolute script path must resolve into this home.
            script = (self.home / ".claude/statusline.py").as_posix()
            self.assertIn(script, command)
            self.assertIn(Path(sys.executable).as_posix(), command)

    def test_idempotent(self) -> None:
        self._run_install()
        out = self._run_install()
        # On second run every line should be a no-op: ok: ... for every managed
        # file whose content already matches the template.
        changed = [
            line for line in out.splitlines()
            if line
            and not line.startswith("ok:")
            and not line.startswith("Install ")
        ]
        self.assertEqual(changed, [], f"unexpected change lines: {changed}")

    def test_prunes_orphan_in_managed_skill_on_reinstall(self) -> None:
        self._run_install()
        # Any nested dir of a managed skill exercises the same prune path; pick one
        # from the templates tree so restructuring a skill cannot silently void this.
        skills_root = cli.REPO_ROOT / "templates" / "skills"
        nested = next(
            (
                path
                for path in sorted(skills_root.glob("*/*"))
                if path.is_dir() and any(path.glob("*.md"))
            ),
            None,
        )
        self.assertIsNotNone(nested, "no managed skill has a nested directory")
        assert nested is not None
        orphan = (
            self.home / ".claude/skills" / nested.relative_to(skills_root) / "__orphan__.md"
        )
        orphan.write_text("stale", encoding="utf-8")
        out = self._run_install()
        self.assertFalse(orphan.exists(), "orphan in a managed skill must be pruned")
        self.assertTrue(orphan.with_name("__orphan__.md.bak").exists())
        self.assertIn("pruned:", out)

    def test_install_deletes_legacy_skill_and_backup(self) -> None:
        legacy_name = "commit"
        roots = [self.home / ".claude/skills", self.home / ".agents/skills"]
        for root in roots:
            for source_name in (legacy_name, f"{legacy_name}.bak"):
                source = root / source_name
                source.mkdir(parents=True)
                (source / "SKILL.md").write_text(source_name, encoding="utf-8")
            archive = root.parent / "retired-skills" / legacy_name
            archive.mkdir(parents=True)
            (archive / "SKILL.md").write_text("archive", encoding="utf-8")

        self._run_install()

        for root in roots:
            self.assertTrue((root / f"km-{legacy_name}/SKILL.md").is_file())
            self.assertFalse((root / legacy_name).exists())
            self.assertFalse((root / f"{legacy_name}.bak").exists())
            self.assertFalse((root.parent / "retired-skills").exists())

    def test_install_retires_decommissioned_config_with_backup(self) -> None:
        rel = cli.DECOMMISSIONED_FILES[0]
        legacy = self.home / rel
        legacy.parent.mkdir(parents=True)
        legacy.write_text("stale", encoding="utf-8")

        out = self._run_install()

        self.assertFalse(legacy.exists())
        self.assertTrue(legacy.with_name(legacy.name + ".bak").exists())
        self.assertIn("removed (obsolete config):", out)

    def test_install_preserves_user_added_skill(self) -> None:
        self._run_install()
        user_skill = self.home / ".claude/skills/__my_custom__/SKILL.md"
        user_skill.parent.mkdir(parents=True, exist_ok=True)
        user_skill.write_text("mine", encoding="utf-8")
        self._run_install()
        self.assertTrue(
            user_skill.exists(), "a user-added top-level skill must never be pruned"
        )

    def test_settings_user_value_preserved_on_rerun(self) -> None:
        self._run_install()
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["theme"] = "user-pick"
        settings.write_text(json.dumps(data), encoding="utf-8")
        self._run_install()
        merged = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(merged["theme"], "user-pick")

    def test_does_not_create_the_qwen_directory(self) -> None:
        # Qwen Code is opt-in: a plain install must not even create ~/.qwen.
        self._run_install()
        self.assertFalse((self.home / ".qwen").exists())

    def test_global_guidelines_installed_as_template_copies(self) -> None:
        self._run_install()
        specs = _global_guideline_specs()
        self.assertTrue(specs, "expected the global guideline specs")
        for spec in specs:
            dest = self.home / spec.dest_rel
            src = cli.REPO_ROOT / spec.src_rel
            self.assertTrue(dest.is_file(), f"missing: {dest}")
            self.assertEqual(
                dest.read_bytes(), src.read_bytes(), f"not a template copy: {dest}"
            )

    def test_codex_profiles_installed_as_top_level_config_files(self) -> None:
        self._run_install()
        expected = {
            ".codex/readonly.config.toml",
        }
        specs = _codex_profile_specs()
        self.assertEqual({s.dest_rel for s in specs}, expected)
        for spec in specs:
            dest = self.home / spec.dest_rel
            src = cli.REPO_ROOT / spec.src_rel
            self.assertTrue(dest.is_file(), f"missing: {dest}")
            self.assertEqual(dest.read_bytes(), src.read_bytes())

    @unittest.skipIf(tomllib is None, "tomllib is available on Python 3.11+")
    def test_codex_model_defaults_and_managed_efforts(self) -> None:
        base = tomllib.loads(
            (cli.REPO_ROOT / "templates/config.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(base["model"], "gpt-5.6-sol")
        self.assertEqual(base["model_reasoning_effort"], "high")
        self.assertEqual(base["plan_mode_reasoning_effort"], "high")
        self.assertEqual(base["personality"], "pragmatic")
        self.assertEqual(base["model_verbosity"], "low")

        managed_efforts = {
            data[key]
            for path in (
                cli.REPO_ROOT / "templates/config.toml",
                cli.REPO_ROOT / "templates/codex/readonly.config.toml",
            )
            for data in [tomllib.loads(path.read_text(encoding="utf-8"))]
            for key in ("model_reasoning_effort", "plan_mode_reasoning_effort")
            if key in data
        }
        self.assertTrue(managed_efforts.isdisjoint({"low", "ultra"}))

    def test_codex_rules_installed(self) -> None:
        self._run_install()
        rules = self.home / ".codex/rules/default.rules"
        self.assertTrue(rules.is_file(), f"missing: {rules}")
        self.assertEqual(
            rules.read_bytes(),
            (cli.REPO_ROOT / "templates/codex-rules/default.rules").read_bytes(),
        )

    def test_codex_default_config_is_the_fully_trusted_baseline(self) -> None:
        base = (cli.REPO_ROOT / "templates/config.toml").read_text(encoding="utf-8")
        self.assertIn('approval_policy = "never"', base)
        self.assertIn('sandbox_mode = "danger-full-access"', base)
        files = [
            cli.REPO_ROOT / spec.src_rel
            for spec in cli.TEMPLATE_FILES
            if spec.dest_rel.startswith(".codex/") and spec.dest_rel.endswith(".toml")
        ]
        offenders = [
            path.relative_to(cli.REPO_ROOT).as_posix()
            for path in files
            if 'approval_policy = "' in path.read_text(encoding="utf-8")
            and 'approval_policy = "never"' not in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])

    def test_global_guidelines_overwritten_when_present(self) -> None:
        # Machine-local edits belong in a *.local.md; the guideline files
        # themselves are refreshed from the template so repo edits propagate.
        for spec in _global_guideline_specs():
            dest = self.home / spec.dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("stale local edit", encoding="utf-8")
        out = self._run_install()
        for spec in _global_guideline_specs():
            dest = self.home / spec.dest_rel
            src = cli.REPO_ROOT / spec.src_rel
            # The user's content is replaced with the template, backed up to .bak.
            self.assertEqual(dest.read_bytes(), src.read_bytes())
            bak = dest.with_name(dest.name + ".bak")
            self.assertTrue(bak.exists(), f"missing bak: {bak}")
            self.assertEqual(bak.read_text(encoding="utf-8"), "stale local edit")
        self.assertIn("replaced:", out)

    def test_dir_perms_0700_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        self._run_install()
        for sub in cli.INSTALL_HOME_DIRS:
            mode = (self.home / sub).stat().st_mode & 0o777
            self.assertEqual(mode, 0o700)

    def test_file_perms_match_spec_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        self._run_install()
        for spec in cli.TEMPLATE_FILES:
            dest = self.home / spec.dest_rel
            mode = dest.stat().st_mode & 0o777
            self.assertEqual(mode, spec.mode, f"{dest} mode={oct(mode)} expected {oct(spec.mode)}")

    def test_converges_mode_drift_so_verify_passes_again(self) -> None:
        # An external tool rewriting its own config with a wider mode must not
        # leave drift that install cannot repair: install says "done" while
        # verify says "drift", and re-running changes nothing.
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        self._run_install()
        widened = [
            self.home / cli.SETTINGS_DEST_REL,
            self.home / cli.TEMPLATE_FILES[0].dest_rel,
            self.home / cli.TEMPLATE_TREES[0].dest_rel / "python-coding-style.md",
        ]
        for path in widened:
            self.assertTrue(path.is_file(), f"missing: {path}")
            path.chmod(0o644)

        out = self._run_install()

        for path in widened:
            self.assertEqual(
                path.stat().st_mode & 0o777, cli.FILE_MODE, f"mode not restored: {path}"
            )
            self.assertFalse(path.with_name(path.name + ".bak").exists())
            self.assertIn(f"mode: {path}", out, "a permission change is reported")
        self.assertNotIn("merged:", out, "a mode fix must not rewrite content")
        self.assertNotIn("replaced:", out, "a mode fix must not rewrite content")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertEqual(report.fail_count(), 0, f"unexpected failures: {report.failures}")

    def test_symlinked_settings_becomes_a_managed_file_keeping_user_keys(self) -> None:
        # verify checks the mode through the link but the installer refuses to
        # chmod a link target, so a symlinked destination is one install and
        # verify would never agree on.
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        self._run_install()
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["theme"] = "user-pick"
        real = self.home / ".claude/real-settings.json"
        real.write_text(cli.render(data), encoding="utf-8")
        real.chmod(0o644)
        settings.unlink()
        settings.symlink_to(real)
        # A backup of a genuinely older state must survive: the content here is
        # unchanged, so there is nothing worth spending the single .bak on.
        bak = settings.with_name(settings.name + ".bak")
        bak.write_text('{"precious": "earlier state"}', encoding="utf-8")

        out = self._run_install()

        self.assertIn("materialized:", out, "replacing a symlink is named as such")
        self.assertNotIn(f"merged: {settings}", out)
        self.assertNotIn(f"backup: {settings}.bak", out)
        self.assertEqual(
            json.loads(bak.read_text(encoding="utf-8")), {"precious": "earlier state"}
        )
        self.assertFalse(settings.is_symlink(), "a managed destination is a real file")
        self.assertEqual(settings.stat().st_mode & 0o777, cli.FILE_MODE)
        merged = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(merged["theme"], "user-pick", "user keys must survive")
        self.assertIn("statusLine", merged)
        self.assertEqual(
            real.stat().st_mode & 0o777, 0o644, "the link target is not chmod-ed"
        )
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertEqual(report.fail_count(), 0, f"unexpected failures: {report.failures}")

    def test_runs_to_completion(self) -> None:
        # Lower-level boundary guarantees are covered by InstallTreeTests.
        self._run_install()


# --------------------------------------------------------------------------- #
# clean
# --------------------------------------------------------------------------- #
class CleanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="clean-test-"))
        self.layout = cli.home_layout(self.home)
        with patch("sys.stdout", new=StringIO()):
            cli.install(self.layout)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _run_clean(self) -> str:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.clean(self.layout)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_removes_managed_files(self) -> None:
        self._run_clean()
        for spec in cli.TEMPLATE_FILES:
            dest = self.home / spec.dest_rel
            self.assertFalse(dest.exists(), f"still present: {dest}")

    def test_removes_managed_trees(self) -> None:
        self._run_clean()
        for tspec in cli.TEMPLATE_TREES:
            self.assertFalse((self.home / tspec.dest_rel).exists())

    def test_creates_bak_for_each(self) -> None:
        self._run_clean()
        for spec in cli.TEMPLATE_FILES:
            bak = self.home / (spec.dest_rel + ".bak")
            self.assertTrue(bak.exists(), f"missing bak: {bak}")

    def test_preserves_settings_json(self) -> None:
        self._run_clean()
        settings = self.home / cli.SETTINGS_DEST_REL
        self.assertTrue(
            settings.exists(),
            "clean() must not remove ~/.claude/settings.json (carries user values)",
        )

    def test_skip_when_already_absent(self) -> None:
        self._run_clean()
        out = self._run_clean()
        self.assertIn("skip:", out)


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #
class VerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="verify-test-"))
        self.layout = cli.home_layout(self.home)
        with patch("sys.stdout", new=StringIO()):
            cli.install(self.layout)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_clean_install_verifies(self) -> None:
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertEqual(report.fail_count(), 0, f"unexpected failures: {report.failures}")
        self.assertGreater(report.checks, 0)

    def test_missing_file_detected(self) -> None:
        target = self.home / _verified_spec().dest_rel
        target.unlink()
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertGreater(report.fail_count(), 0)
        self.assertTrue(any("missing" in m for m in report.failures))

    def test_drift_detected(self) -> None:
        target = self.home / _verified_spec().dest_rel
        target.write_text("not the template content", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(any("drift" in m for m in report.failures))

    def test_mode_drift_detected_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        target = self.home / _verified_spec().dest_rel
        target.chmod(0o644)
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(any("mode drift" in m for m in report.failures))

    def test_global_guideline_drift_flagged(self) -> None:
        # The guideline files are pure template copies, so an edit to one is
        # drift that verify must report (machine-local rules go in a *.local.md).
        specs = _global_guideline_specs()
        self.assertTrue(specs, "expected the global guideline specs")
        for spec in specs:
            (self.home / spec.dest_rel).write_text(
                "my own global guideline", encoding="utf-8"
            )
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        for spec in specs:
            dest = self.home / spec.dest_rel
            self.assertTrue(
                any("drift" in m and str(dest) in m for m in report.failures),
                report.failures,
            )

    def test_settings_missing_template_key_detected(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        removed_key = next(iter(data))
        del data[removed_key]
        settings.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(
            any("settings missing template key" in m and removed_key in m for m in report.failures),
            report.failures,
        )

    def test_settings_invalid_json_detected(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        settings.write_text("{not valid", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(any("invalid json" in m for m in report.failures))

    def test_settings_non_object_detected(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        settings.write_text(json.dumps(["not", "object"]), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(any("settings.json must be a JSON object" in m for m in report.failures))

    def test_settings_existing_key_override_is_allowed(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        override_key = next(iter(data))
        data[override_key] = "user override"
        settings.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertFalse(any(override_key in m for m in report.failures), report.failures)

    def test_qwen_component_absent_still_verifies(self) -> None:
        # ~/.qwen is not part of the default selection, so its absence — or any
        # drift inside it — is none of a plain verify's business.
        qwen = self.home / ".qwen"
        (qwen / "skills").mkdir(parents=True)
        (qwen / "QWEN.md").write_text("drifted", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertEqual(report.fail_count(), 0, f"unexpected failures: {report.failures}")


# --------------------------------------------------------------------------- #
# layout command arguments
# --------------------------------------------------------------------------- #
class LayoutArgumentTests(unittest.TestCase):
    def test_absent_flags_select_the_base_component_set(self) -> None:
        parsed = cli.parse_layout_args([])
        self.assertIsNone(parsed.claude_dir)
        self.assertFalse(parsed.include_qwen)

    def test_separate_value(self) -> None:
        self.assertEqual(cli.parse_layout_args(["--claude-dir", "/tmp/x"]).claude_dir, "/tmp/x")

    def test_equals_form(self) -> None:
        self.assertEqual(cli.parse_layout_args(["--claude-dir=/tmp/x"]).claude_dir, "/tmp/x")

    def test_missing_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            cli.parse_layout_args(["--claude-dir"])

    def test_unknown_argument_raises(self) -> None:
        # Silently ignoring it would install into $HOME while the user believes
        # a different directory was targeted.
        with self.assertRaises(ValueError):
            cli.parse_layout_args(["--claud-dir", "/tmp/x"])

    def test_qwen_flag_sets_the_component(self) -> None:
        self.assertTrue(cli.parse_layout_args(["--qwen"]).include_qwen)

    def test_claude_dir_with_qwen_raises(self) -> None:
        # One command must not mutate two unrelated roots.
        with self.assertRaises(ValueError):
            cli.parse_layout_args(["--claude-dir", "/tmp/x", "--qwen"])

    def test_claude_dir_does_not_swallow_the_next_option(self) -> None:
        # Otherwise `--claude-dir --qwen` installs into a literal ./--qwen and
        # never reaches the conflict check.
        for args in (["--claude-dir", "--qwen"], ["--claude-dir=--qwen"]):
            with self.subTest(args=args), self.assertRaises(ValueError):
                cli.parse_layout_args(args)

    def test_directory_starting_with_a_dash_can_still_be_named(self) -> None:
        self.assertEqual(cli.parse_layout_args(["--claude-dir", "./-x"]).claude_dir, "./-x")


class ResolveClaudeDirTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="resolve-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_expands_tilde(self) -> None:
        with patch.dict(os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)}):
            resolved = cli.resolve_claude_dir("~/.claude-sub", self.home)
        self.assertEqual(resolved, (self.home / ".claude-sub").resolve())

    def test_normalises_dot_segments(self) -> None:
        resolved = cli.resolve_claude_dir(str(self.home / "sub" / ".." / "sub"), self.home)
        self.assertTrue(resolved.is_absolute())
        self.assertEqual(resolved, (self.home / "sub").resolve())

    def test_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            cli.resolve_claude_dir("   ", self.home)

    def test_rejects_home_itself(self) -> None:
        with self.assertRaises(ValueError):
            cli.resolve_claude_dir(str(self.home), self.home)

    def test_rejects_filesystem_root(self) -> None:
        root = Path(self.home.anchor)
        with self.assertRaises(ValueError):
            cli.resolve_claude_dir(str(root), self.home)

    def test_rejects_existing_file(self) -> None:
        target = self.home / "notes.txt"
        target.write_text("mine", encoding="utf-8")
        with self.assertRaises(ValueError):
            cli.resolve_claude_dir(str(target), self.home)

    def test_layout_for_without_flag_is_home_layout(self) -> None:
        layout = cli.layout_for([], self.home)
        self.assertEqual(layout.root, self.home)
        self.assertEqual(layout.description, cli.HOME_DESCRIPTION)

    def test_layout_for_ignores_claude_config_dir_env(self) -> None:
        # An `install` run from a shell that exports CLAUDE_CONFIG_DIR must still
        # target ~/.claude; redirecting the install stays an explicit act.
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.home / ".claude-sub")}):
            layout = cli.layout_for([], self.home)
        self.assertEqual(layout.root, self.home)


# --------------------------------------------------------------------------- #
# --claude-dir: layout derivation
# --------------------------------------------------------------------------- #
class ClaudeDirLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path("/home/user")
        self.target = self.home / ".claude-sub"
        self.layout = cli.claude_dir_layout(self.target, self.home)

    def test_root_is_the_only_managed_dir(self) -> None:
        self.assertEqual(self.layout.managed_dirs, (self.target,))

    def test_destinations_sit_directly_under_the_target(self) -> None:
        dests = [s.dest_rel for s in self.layout.files] + [
            s.dest_rel for s in self.layout.trees
        ] + [s.dest_rel for s in self.layout.settings]
        self.assertTrue(dests)
        for dest_rel in dests:
            self.assertFalse(
                dest_rel.startswith("."), f"still home-relative: {dest_rel}"
            )

    def test_carries_the_whole_claude_slice_of_the_home_manifest(self) -> None:
        # A sub-profile must receive exactly what ~/.claude receives.
        expected_files = {
            s.src_rel for s in cli.TEMPLATE_FILES if s.dest_rel.startswith(".claude/")
        }
        expected_trees = {
            s.src_rel for s in cli.TEMPLATE_TREES if s.dest_rel.startswith(".claude/")
        }
        self.assertEqual({s.src_rel for s in self.layout.files}, expected_files)
        self.assertEqual({s.src_rel for s in self.layout.trees}, expected_trees)
        self.assertEqual(
            [s.dest_rel for s in self.layout.settings], ["settings.json"]
        )

    def test_excludes_destinations_of_other_tools(self) -> None:
        # Codex / Qwen / shared-agent files are addressed by their own tools and
        # are unaffected by CLAUDE_CONFIG_DIR.
        all_dests = (
            [s.dest_rel for s in self.layout.files]
            + [s.dest_rel for s in self.layout.trees]
            + [s.dest_rel for s in self.layout.settings]
        )
        for other in (".codex", ".qwen", ".agents"):
            self.assertFalse(any(other in dest for dest in all_dests), all_dests)

    def test_modes_are_inherited_from_the_home_manifest(self) -> None:
        by_src = {s.src_rel: s for s in cli.TEMPLATE_FILES}
        for spec in self.layout.files:
            self.assertEqual(spec.mode, by_src[spec.src_rel].mode)
            self.assertEqual(spec.is_executable, by_src[spec.src_rel].is_executable)


# --------------------------------------------------------------------------- #
# --claude-dir: install / verify / clean
# --------------------------------------------------------------------------- #
class ClaudeDirInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="claude-dir-home-"))
        self.target = self.home / ".claude-sub"
        self.layout = cli.claude_dir_layout(self.target, self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _run_install(self) -> str:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.install(self.layout)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_creates_the_target_directory(self) -> None:
        self._run_install()
        self.assertTrue(self.target.is_dir())
        if cli.is_posix():
            self.assertEqual(self.target.stat().st_mode & 0o777, cli.DIR_MODE)

    def test_deploys_claude_files_at_the_top_level(self) -> None:
        self._run_install()
        for name in ("CLAUDE.md", "statusline.py", "subagent-statusline.py"):
            self.assertTrue((self.target / name).is_file(), f"missing: {name}")
        for name in ("rules", "skills", "output-styles"):
            self.assertTrue((self.target / name).is_dir(), f"missing: {name}")
        self.assertTrue((self.target / "settings.json").is_file())

    def test_content_matches_the_templates(self) -> None:
        self._run_install()
        src = cli.REPO_ROOT / "templates" / "CLAUDE.md"
        self.assertEqual(
            (self.target / "CLAUDE.md").read_bytes(), src.read_bytes()
        )

    def test_leaves_the_home_layout_untouched(self) -> None:
        self._run_install()
        for sub in cli.INSTALL_HOME_DIRS + cli.QWEN_HOME_DIRS:
            self.assertFalse((self.home / sub).exists(), f"unexpected: {sub}")
        self.assertFalse((self.target / ".claude").exists())

    def test_statusline_command_points_at_the_target(self) -> None:
        self._run_install()
        data = json.loads((self.target / "settings.json").read_text(encoding="utf-8"))
        command = data["statusLine"]["command"]
        script = self.target / "statusline.py"
        if cli.is_posix():
            # The target lives under the home, so the tilde form addresses it.
            self.assertEqual(command, "~/.claude-sub/statusline.py")
        else:
            self.assertIn(script.as_posix(), command)
            self.assertIn(Path(sys.executable).as_posix(), command)

    def test_statusline_command_is_absolute_for_a_target_outside_home(self) -> None:
        outside = self.home / "elsewhere" / "profile"
        layout = cli.claude_dir_layout(outside, Path("/nonexistent-home"))
        with patch("sys.stdout", new=StringIO()):
            cli.install(layout)
        data = json.loads((outside / "settings.json").read_text(encoding="utf-8"))
        command = data["statusLine"]["command"]
        script = outside / "statusline.py"
        if cli.is_posix():
            self.assertEqual(command, script.as_posix())
        else:
            self.assertIn(script.as_posix(), command)

    def test_modes_match_the_manifest_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        self._run_install()
        for spec in self.layout.files:
            dest = self.target / spec.dest_rel
            self.assertEqual(dest.stat().st_mode & 0o777, spec.mode, str(dest))
        self.assertEqual(
            (self.target / "settings.json").stat().st_mode & 0o777, cli.FILE_MODE
        )

    def test_idempotent(self) -> None:
        self._run_install()
        out = self._run_install()
        changed = [
            line
            for line in out.splitlines()
            if line and not line.startswith("ok:") and not line.startswith("Install ")
        ]
        self.assertEqual(changed, [], f"unexpected change lines: {changed}")

    def test_settings_user_value_preserved_on_rerun(self) -> None:
        self._run_install()
        settings = self.target / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["theme"] = "user-pick"
        settings.write_text(json.dumps(data), encoding="utf-8")
        self._run_install()
        merged = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(merged["theme"], "user-pick")

    def test_prunes_orphan_in_managed_skill_on_reinstall(self) -> None:
        self._run_install()
        skills_root = cli.REPO_ROOT / "templates" / "skills"
        nested = next(
            (
                path
                for path in sorted(skills_root.glob("*/*"))
                if path.is_dir() and any(path.glob("*.md"))
            ),
            None,
        )
        self.assertIsNotNone(nested, "no managed skill has a nested directory")
        assert nested is not None
        orphan = (
            self.target / "skills" / nested.relative_to(skills_root) / "__orphan__.md"
        )
        orphan.write_text("stale", encoding="utf-8")
        self._run_install()
        self.assertFalse(orphan.exists())
        self.assertTrue(orphan.with_name("__orphan__.md.bak").exists())

    def test_preserves_user_added_skill(self) -> None:
        self._run_install()
        user_skill = self.target / "skills" / "__my_custom__" / "SKILL.md"
        user_skill.parent.mkdir(parents=True, exist_ok=True)
        user_skill.write_text("mine", encoding="utf-8")
        self._run_install()
        self.assertTrue(user_skill.exists())

    def test_deletes_decommissioned_skill(self) -> None:
        legacy = cli.DECOMMISSIONED_SKILLS[0]
        stale = self.target / "skills" / legacy
        stale.mkdir(parents=True)
        (stale / "SKILL.md").write_text("old", encoding="utf-8")
        self._run_install()
        self.assertFalse(stale.exists())

    def test_verify_passes_after_install(self) -> None:
        self._run_install()
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertEqual(report.fail_count(), 0, f"failures: {report.failures}")
        self.assertGreater(report.checks, 0)

    def test_verify_detects_drift(self) -> None:
        self._run_install()
        (self.target / "CLAUDE.md").write_text("edited", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(any("drift" in m for m in report.failures), report.failures)

    def test_clean_removes_templates_but_keeps_settings(self) -> None:
        self._run_install()
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.clean(self.layout)
        self.assertEqual(rc, 0)
        self.assertIn(str(self.target), out.getvalue())
        for name in ("CLAUDE.md", "statusline.py", "rules", "skills", "output-styles"):
            self.assertFalse((self.target / name).exists(), f"still present: {name}")
        self.assertTrue(
            (self.target / "settings.json").exists(),
            "clean() must keep settings.json (carries user values)",
        )


class ClaudeDirCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="claude-dir-cli-"))
        self.target = self.home / ".claude-sub"

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_install_dispatches_to_the_target(self) -> None:
        with patch("sys.stdout", new=StringIO()):
            rc = cli.main(["cli.py", "install", "--claude-dir", str(self.target)])
        self.assertEqual(rc, 0)
        self.assertTrue((self.target / "CLAUDE.md").is_file())

    def test_verify_dispatches_to_the_target(self) -> None:
        with patch("sys.stdout", new=StringIO()):
            cli.main(["cli.py", "install", f"--claude-dir={self.target}"])
            rc = cli.main(["cli.py", "verify", f"--claude-dir={self.target}"])
        self.assertEqual(rc, 0)

    def test_unknown_option_returns_2_without_installing(self) -> None:
        with patch("sys.stdout", new=StringIO()), patch("sys.stderr", new=StringIO()):
            rc = cli.main(["cli.py", "install", "--claude-dir", str(self.target), "--oops"])
        self.assertEqual(rc, 2)
        self.assertFalse(self.target.exists())

    def test_target_that_is_a_file_returns_2(self) -> None:
        self.target.write_text("mine", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()), patch("sys.stderr", new=StringIO()):
            rc = cli.main(["cli.py", "install", "--claude-dir", str(self.target)])
        self.assertEqual(rc, 2)
        self.assertEqual(self.target.read_text(encoding="utf-8"), "mine")


# --------------------------------------------------------------------------- #
# canonical agent guideline
# --------------------------------------------------------------------------- #
def _guideline_specs() -> list[cli.FileSpec]:
    """Every managed destination that is an agent guideline file."""
    names = {"CLAUDE.md", "AGENTS.md", "QWEN.md"}
    return [
        spec
        for spec in cli.TEMPLATE_FILES + cli.QWEN_TEMPLATE_FILES
        if Path(spec.dest_rel).name in names
    ]


class CanonicalGuidelineTests(unittest.TestCase):
    def test_every_guideline_destination_has_one_source(self) -> None:
        specs = _guideline_specs()
        self.assertEqual(
            {spec.dest_rel for spec in specs},
            {".claude/CLAUDE.md", ".codex/AGENTS.md", ".qwen/QWEN.md"},
        )
        self.assertEqual({spec.src_rel for spec in specs}, {cli.GUIDELINE_TEMPLATE_REL})

    def test_no_second_guideline_source_in_the_repository(self) -> None:
        # A per-tool source template would make it ambiguous which file to edit.
        # Only the guideline file names are constrained: other markdown may live
        # beside the canonical source.
        canonical = Path(cli.GUIDELINE_TEMPLATE_REL)
        guideline_names = {Path(spec.dest_rel).name for spec in _guideline_specs()}
        present = {p.name for p in (cli.REPO_ROOT / canonical.parent).glob("*.md")}
        self.assertEqual(present & guideline_names, {canonical.name})


# --------------------------------------------------------------------------- #
# --qwen: the opt-in Qwen Code component
# --------------------------------------------------------------------------- #
def _snapshot(root: Path) -> dict[str, str | None]:
    """Content of every entry under `root` (None marks a directory)."""
    return {
        path.relative_to(root).as_posix(): (
            None if path.is_dir() else path.read_text(encoding="utf-8")
        )
        for path in sorted(root.rglob("*"))
    }


class QwenComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="qwen-test-"))
        self.base = cli.home_layout(self.home)
        self.layout = cli.home_layout(self.home, include_qwen=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _install(self, layout: cli.Layout) -> str:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.install(layout)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def _seed_foreign_qwen(self) -> dict[str, str | None]:
        """Populate ~/.qwen as an older install would have, and snapshot it."""
        qwen = self.home / ".qwen"
        (qwen / "skills" / "km-commit").mkdir(parents=True)
        (qwen / "skills" / "km-commit" / "SKILL.md").write_text("stale", encoding="utf-8")
        # A decommissioned skill name and an orphan file inside a managed skill:
        # both would be removed by the install-time cleanup if it ran here.
        (qwen / "skills" / "commit").mkdir()
        (qwen / "skills" / "commit" / "SKILL.md").write_text("legacy", encoding="utf-8")
        (qwen / "skills" / "km-commit" / "__orphan__.md").write_text("orphan", encoding="utf-8")
        # The cleanup also deletes a sibling `retired-skills/` next to a managed
        # skills root, which is outside the tree itself.
        (qwen / "retired-skills" / "old").mkdir(parents=True)
        (qwen / "retired-skills" / "old" / "SKILL.md").write_text("archived", encoding="utf-8")
        (qwen / "QWEN.md").write_text("my own guideline", encoding="utf-8")
        (qwen / "settings.json").write_text('{"fastModel": "mine"}', encoding="utf-8")
        return _snapshot(qwen)

    def test_layout_for_flag_selects_the_component(self) -> None:
        layout = cli.layout_for(["--qwen"], self.home)
        self.assertIn(self.home / ".qwen", layout.managed_dirs)
        self.assertEqual(layout.description, cli.HOME_QWEN_DESCRIPTION)

    def test_layout_is_additive(self) -> None:
        # --qwen adds to the usual destinations; it never narrows them.
        for base_specs, qwen_specs in (
            (self.base.files, self.layout.files),
            (self.base.trees, self.layout.trees),
            (self.base.settings, self.layout.settings),
            (self.base.managed_dirs, self.layout.managed_dirs),
        ):
            self.assertEqual(list(qwen_specs[: len(base_specs)]), list(base_specs))
            self.assertGreater(len(qwen_specs), len(base_specs))

    def test_install_deploys_the_managed_artifacts(self) -> None:
        self._install(self.layout)
        self.assertTrue((self.home / ".qwen/QWEN.md").is_file())
        for rel in _skill_docs():
            self.assertTrue((self.home / ".qwen/skills" / rel).is_file(), f"missing: {rel}")
        settings = json.loads(
            (self.home / cli.QWEN_SETTINGS_DEST_REL).read_text(encoding="utf-8")
        )
        self.assertEqual(settings["fastModel"], "qwen3.6-flash")
        self.assertEqual(settings["tools"]["approvalMode"], "auto")

    def test_guideline_is_a_copy_of_the_canonical_template(self) -> None:
        self._install(self.layout)
        canonical = (cli.REPO_ROOT / cli.GUIDELINE_TEMPLATE_REL).read_bytes()
        for dest_rel in (".claude/CLAUDE.md", ".codex/AGENTS.md", ".qwen/QWEN.md"):
            self.assertEqual(
                (self.home / dest_rel).read_bytes(), canonical, f"not a copy: {dest_rel}"
            )

    def test_settings_user_only_key_preserved_on_rerun(self) -> None:
        self._install(self.layout)
        settings = self.home / cli.QWEN_SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["model"] = {"name": "user-model", "reasoningEffort": "high"}
        settings.write_text(json.dumps(data), encoding="utf-8")
        self._install(self.layout)
        merged = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(merged["model"]["name"], "user-model")
        self.assertEqual(merged["fastModel"], "qwen3.6-flash")

    def test_install_is_idempotent(self) -> None:
        self._install(self.layout)
        out = self._install(self.layout)
        changed = [
            line
            for line in out.splitlines()
            if line and not line.startswith("ok:") and not line.startswith("Install ")
        ]
        self.assertEqual(changed, [], f"unexpected change lines: {changed}")

    def test_verify_passes_after_install(self) -> None:
        self._install(self.layout)
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertEqual(report.fail_count(), 0, f"unexpected failures: {report.failures}")

    def test_verify_fails_when_the_component_was_not_installed(self) -> None:
        self._install(self.base)
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(
            any(".qwen" in message for message in report.failures), report.failures
        )

    def test_verify_detects_settings_drift(self) -> None:
        self._install(self.layout)
        settings = self.home / cli.QWEN_SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        del data["fastModel"]
        settings.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.layout)
        self.assertTrue(
            any(
                "settings missing template key" in m and "fastModel" in m
                for m in report.failures
            ),
            report.failures,
        )

    def test_clean_removes_managed_artifacts_but_keeps_settings(self) -> None:
        self._install(self.layout)
        with patch("sys.stdout", new=StringIO()):
            self.assertEqual(cli.clean(self.layout), 0)
        self.assertFalse((self.home / ".qwen/QWEN.md").exists())
        self.assertFalse((self.home / ".qwen/skills").exists())
        self.assertTrue(
            (self.home / cli.QWEN_SETTINGS_DEST_REL).exists(),
            "clean() must not remove ~/.qwen/settings.json (carries user values)",
        )

    def test_first_qwen_install_adopts_the_tree_and_removes_retired_names(self) -> None:
        # The flip side of the no-touch guarantee: once selected, ~/.qwen is a
        # managed tree, so a directory whose name matches a retired skill is
        # deleted outright (no .bak) while a user-added name survives.
        qwen = self.home / ".qwen"
        (qwen / "skills" / "commit").mkdir(parents=True)
        (qwen / "skills" / "commit" / "SKILL.md").write_text("legacy", encoding="utf-8")
        (qwen / "skills" / "__mine__").mkdir()
        (qwen / "skills" / "__mine__" / "SKILL.md").write_text("mine", encoding="utf-8")
        self._install(self.layout)
        self.assertFalse((qwen / "skills" / "commit").exists())
        self.assertFalse((qwen / "skills" / "commit.bak").exists())
        self.assertTrue((qwen / "skills" / "__mine__" / "SKILL.md").is_file())

    def test_plain_install_does_not_retire_files_under_the_unselected_component(self) -> None:
        # A retirement entry pointing into ~/.qwen must not make a plain install
        # reach into a component this layout did not select.
        target = self.home / ".qwen/QWEN.md"
        target.parent.mkdir(parents=True)
        target.write_text("mine", encoding="utf-8")
        with patch.object(cli, "DECOMMISSIONED_FILES", (".qwen/QWEN.md",)):
            self._install(self.base)
        self.assertEqual(target.read_text(encoding="utf-8"), "mine")
        self.assertFalse(target.with_name("QWEN.md.bak").exists())

    def test_plain_install_leaves_an_existing_qwen_untouched(self) -> None:
        # Switching back to the default selection must not migrate ~/.qwen:
        # no prune, no decommissioned-skill cleanup, no settings merge.
        before = self._seed_foreign_qwen()
        self._install(self.base)
        self.assertEqual(_snapshot(self.home / ".qwen"), before)

    def test_plain_clean_leaves_an_existing_qwen_untouched(self) -> None:
        before = self._seed_foreign_qwen()
        with patch("sys.stdout", new=StringIO()):
            self.assertEqual(cli.clean(self.base), 0)
        self.assertEqual(_snapshot(self.home / ".qwen"), before)


class QwenCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="qwen-cli-"))
        self.target = self.home / ".claude-sub"

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _main(self, *args: str) -> tuple[int, str]:
        with patch.object(cli.Path, "home", return_value=self.home), patch(
            "sys.stdout", new=StringIO()
        ), patch("sys.stderr", new=StringIO()) as err:
            rc = cli.main(["cli.py", *args])
        return rc, err.getvalue()

    def test_install_without_the_flag_skips_qwen(self) -> None:
        rc, _ = self._main("install")
        self.assertEqual(rc, 0)
        self.assertTrue((self.home / ".claude").is_dir())
        self.assertFalse((self.home / ".qwen").exists())

    def test_install_with_the_flag_adds_qwen(self) -> None:
        rc, _ = self._main("install", "--qwen")
        self.assertEqual(rc, 0)
        self.assertTrue((self.home / ".claude").is_dir())
        self.assertTrue((self.home / ".qwen/QWEN.md").is_file())

    def test_verify_after_a_qwen_install(self) -> None:
        self._main("install", "--qwen")
        self.assertEqual(self._main("verify", "--qwen")[0], 0)
        self.assertEqual(self._main("verify")[0], 0)

    def test_plain_verify_passes_without_qwen(self) -> None:
        self._main("install")
        self.assertEqual(self._main("verify")[0], 0)
        self.assertEqual(self._main("verify", "--qwen")[0], 1)

    def test_claude_dir_with_qwen_is_a_usage_error_before_any_mutation(self) -> None:
        for command in ("install", "verify", "clean"):
            with self.subTest(command=command):
                rc, err = self._main(command, "--claude-dir", str(self.target), "--qwen")
                self.assertEqual(rc, 2)
                self.assertIn("--qwen", err)
                self.assertEqual(list(self.home.iterdir()), [])

    def test_claude_dir_missing_its_value_installs_nowhere(self) -> None:
        # `--claude-dir --qwen` used to consume the flag as the directory name
        # and install into a literal ./--qwen, never reaching the conflict check.
        cwd = Path.cwd()
        os.chdir(self.home)
        try:
            rc, err = self._main("install", "--claude-dir", "--qwen")
        finally:
            os.chdir(cwd)
        self.assertEqual(rc, 2)
        self.assertIn("--claude-dir", err)
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
