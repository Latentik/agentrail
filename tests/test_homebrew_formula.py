from pathlib import Path

from scripts.render_homebrew_formula import FORMULA_TEMPLATE


def test_formula_template_contains_arch_sections() -> None:
    assert "on_arm do" in FORMULA_TEMPLATE
    assert "on_intel do" not in FORMULA_TEMPLATE
    assert "agentrail --version" in FORMULA_TEMPLATE
    assert 'libexec.install Dir["*"]' in FORMULA_TEMPLATE
    assert 'bin.install_symlink libexec/"agentrail"' in FORMULA_TEMPLATE


def test_formula_render_can_be_formatted_to_path(tmp_path: Path) -> None:
    output = tmp_path / "agentrail.rb"
    output.write_text(
        FORMULA_TEMPLATE.format(
            version="0.1.6",
            owner_repo="Latentik/agentrail",
            arm_url="https://example.invalid/arm.tgz",
            arm_sha="a" * 64,
            linux_blocks="",
        ),
        encoding="utf-8",
    )
    rendered = output.read_text(encoding="utf-8")
    assert 'version "0.1.6"' in rendered
    assert 'homepage "https://github.com/Latentik/agentrail"' in rendered


def test_formula_with_linux_blocks(tmp_path: Path) -> None:
    linux = '\n  on_linux do\n    on_intel do\n      url "https://example.invalid/linux.tgz"\n      sha256 "b" * 64\n    end\n  end'
    output = tmp_path / "agentrail.rb"
    output.write_text(
        FORMULA_TEMPLATE.format(
            version="0.1.6",
            owner_repo="Latentik/agentrail",
            arm_url="https://example.invalid/arm.tgz",
            arm_sha="a" * 64,
            linux_blocks=linux,
        ),
        encoding="utf-8",
    )
    rendered = output.read_text(encoding="utf-8")
    assert "on_linux" in rendered
    assert "on_intel" in rendered
    assert "linux.tgz" in rendered
