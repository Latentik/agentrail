"""Assemble a Homebrew-friendly macOS release bundle."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tarfile
from pathlib import Path


def build_bundle(dist_dir: Path, output_dir: Path, version: str) -> tuple[Path, Path]:
    binary_path = dist_dir / "agentrail"
    internal_path = dist_dir / "_internal"
    if not binary_path.is_file():
        raise FileNotFoundError(f"Missing PyInstaller binary: {binary_path}")
    if not internal_path.is_dir():
        raise FileNotFoundError(f"Missing PyInstaller support directory: {internal_path}")

    bundle_root = output_dir / "bundle"
    bundle_dir = bundle_root / "agentrail"
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_dir.mkdir(parents=True)

    shutil.copy2(binary_path, bundle_dir / "agentrail")
    shutil.copytree(internal_path, bundle_dir / "_internal")

    archive_name = f"agentrail-v{version}-macos-arm64.tar.gz"
    archive_path = output_dir / archive_name
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(bundle_dir, arcname="agentrail")

    sha_path = output_dir / f"{archive_name}.sha256"
    sha_path.write_text(f"{sha256_file(archive_path)}  {archive_name}\n", encoding="utf-8")
    return archive_path, sha_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    build_bundle(Path(args.dist_dir), Path(args.output_dir), args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
