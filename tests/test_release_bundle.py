import tarfile
from pathlib import Path

from scripts.build_release_bundle import build_bundle


def test_build_bundle_packages_binary_and_internal_dir(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "agentrail").write_text("binary", encoding="utf-8")
    internal_dir = dist_dir / "_internal"
    internal_dir.mkdir()
    (internal_dir / "Python").write_text("runtime", encoding="utf-8")

    archive_path, sha_path = build_bundle(dist_dir=dist_dir, output_dir=tmp_path, version="0.1.4")

    assert archive_path.name == "agentrail-v0.1.4-macos-arm64.tar.gz"
    assert sha_path.name == "agentrail-v0.1.4-macos-arm64.tar.gz.sha256"
    members = []
    with tarfile.open(archive_path, "r:gz") as archive:
        members = sorted(archive.getnames())

    assert "agentrail" in members
    assert "agentrail/_internal" in members
    assert "agentrail/_internal/Python" in members
    assert "agentrail/agentrail" in members

    sha_contents = sha_path.read_text(encoding="utf-8")
    assert "agentrail-v0.1.4-macos-arm64.tar.gz" in sha_contents
