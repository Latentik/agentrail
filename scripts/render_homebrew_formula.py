"""Render a Homebrew formula for agentrail release assets."""

from __future__ import annotations

import argparse
from pathlib import Path

FORMULA_TEMPLATE = '''class Agentrail < Formula
  desc "Portable coding-agent handoff CLI"
  homepage "https://github.com/{owner_repo}"
  version "{version}"
  license "Apache-2.0"

  on_macos do
    on_arm do
      url "{arm_url}"
      sha256 "{arm_sha}"
    end
  end
{linux_blocks}

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"agentrail"
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/agentrail --version")
  end
end
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--owner-repo", required=True)
    parser.add_argument("--arm-url", required=True)
    parser.add_argument("--arm-sha", required=True)
    parser.add_argument("--linux-x86_64-url", default="")
    parser.add_argument("--linux-x86_64-sha", default="")
    parser.add_argument("--linux-arm64-url", default="")
    parser.add_argument("--linux-arm64-sha", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    linux_blocks = ""
    if args.linux_x86_64_url and args.linux_x86_64_sha:
        linux_blocks += '\n  on_linux do\n    on_intel do\n      url "{}"\n      sha256 "{}"\n    end\n  end'.format(
            args.linux_x86_64_url, args.linux_x86_64_sha
        )
    if args.linux_arm64_url and args.linux_arm64_sha:
        linux_blocks += '\n  on_linux do\n    on_arm do\n      url "{}"\n      sha256 "{}"\n    end\n  end'.format(
            args.linux_arm64_url, args.linux_arm64_sha
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        FORMULA_TEMPLATE.format(
            version=args.version,
            owner_repo=args.owner_repo,
            arm_url=args.arm_url,
            arm_sha=args.arm_sha,
            linux_blocks=linux_blocks,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
