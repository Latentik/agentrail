import tarfile
from pathlib import Path

from scripts.build_release_bundle import build_bundle


def _read_members(archive_path: Path) -> list[str]:
    with tarfile.open(archive_path, "r:gz") as archive:
        return sorted(archive.getnames())


def test_build_bundle_packages_onedir_layout(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    bundle_dir = dist_dir / "agentrail"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "agentrail").write_text("binary", encoding="utf-8")
    internal_dir = bundle_dir / "_internal"
    internal_dir.mkdir()
    (internal_dir / "Python").write_text("runtime", encoding="utf-8")

    archive_path, sha_path = build_bundle(dist_dir=dist_dir, output_dir=tmp_path, version="0.1.6")

    assert archive_path.name == "agentrail-v0.1.6-macos-arm64.tar.gz"
    assert sha_path.name == "agentrail-v0.1.6-macos-arm64.tar.gz.sha256"


def test_build_bundle_linux_platform(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    bundle_dir = dist_dir / "agentrail"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "agentrail").write_text("binary", encoding="utf-8")
    internal_dir = bundle_dir / "_internal"
    internal_dir.mkdir()
    (internal_dir / "Python").write_text("runtime", encoding="utf-8")

    archive_path, sha_path = build_bundle(
        dist_dir=dist_dir, output_dir=tmp_path, version="0.1.6", platform="linux-x86_64"
    )

    assert archive_path.name == "agentrail-v0.1.6-linux-x86_64.tar.gz"
    assert sha_path.name == "agentrail-v0.1.6-linux-x86_64.tar.gz.sha256"
    members = _read_members(archive_path)
    assert "agentrail" in members
    assert "agentrail/_internal" in members
    assert "agentrail/_internal/Python" in members
    assert "agentrail/agentrail" in members
    assert "agentrail-v0.1.6-linux-x86_64.tar.gz" in sha_path.read_text(encoding="utf-8")


def test_build_bundle_accepts_flat_layout(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "agentrail").write_text("binary", encoding="utf-8")
    internal_dir = dist_dir / "_internal"
    internal_dir.mkdir()
    (internal_dir / "Python").write_text("runtime", encoding="utf-8")

    archive_path, _ = build_bundle(dist_dir=dist_dir, output_dir=tmp_path, version="0.1.6")

    members = _read_members(archive_path)
    assert "agentrail/_internal/Python" in members
