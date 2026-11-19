"""tools/CreateUpdateRelease.py: the files of a new release, built without touching Git or the working tree."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("release_tool", ROOT / "tools" / "CreateUpdateRelease.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

CHANGELOG = "# 🗓️ CHANGELOG\n\n---\n\n## Release: v0.1.0\n### Release Date: 2026-11-19\n#### 🌟 New Features:\n- **X**\n"


def test_validate_inputs():
    assert rt.validate_inputs("0.2.0", "2026-12-01") is None
    assert rt.validate_inputs("0.2", "2026-12-01")
    assert rt.validate_inputs("0.2.0-rc1", "2026-12-01")          # the image is only built for X.Y.Z branches
    assert rt.validate_inputs("0.2.0", "2026-02-30")


def test_new_release_goes_on_top_with_empty_sections():
    out = rt.add_changelog_release(CHANGELOG, "0.2.0", "2026-12-01")
    assert out.index("## Release: v0.2.0") < out.index("## Release: v0.1.0")
    for s in rt.RELEASE_SECTIONS:
        assert s in out
    with pytest.raises(RuntimeError):
        rt.add_changelog_release(out, "0.2.0", "2026-12-01")
    es = rt.add_changelog_release(CHANGELOG, "0.2.0", "2026-12-01", rt.RELEASE_SECTIONS_ES)
    assert "#### 🌟 Novedades:" in es


def test_update_header_pyproject_and_android():
    out = rt.replace_current_changelog_metadata(CHANGELOG, "0.1.1", "2026-11-20")
    assert "## Release: v0.1.1\n### Release Date: 2026-11-20" in out
    assert 'version = "0.3.0"' in rt.replace_pyproject_version('[project]\nname = "x"\nversion = "0.1.0"\n', "0.3.0")
    g = 'versionName = "0.1." + (System.getenv("BODYLENS_ANDROID_BUILD") ?: "0")'
    assert rt.replace_android_version(g, "1.4.2").startswith('versionName = "1.4." +')


def test_real_files_build_without_writing():
    before = {p: p.read_text(encoding="utf-8") for p in (rt.PYPROJECT_PATH, rt.CHANGELOG_PATH, rt.CHANGELOG_ES_PATH)}
    version, _ = rt.read_release_metadata()
    major, minor, patch = map(int, version.split("."))
    files = rt.release_file_contents(f"{major}.{minor}.{patch + 1}", "2030-01-01", create_changelog_release=True)
    assert f"## Release: v{major}.{minor}.{patch + 1}" in files[rt.CHANGELOG_ES_PATH]
    assert {p: p.read_text(encoding="utf-8") for p in before} == before        # nothing written
