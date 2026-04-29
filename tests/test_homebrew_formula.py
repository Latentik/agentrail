from pathlib import Path

from scripts.render_homebrew_formula import FORMULA_TEMPLATE


def test_formula_template_contains_arch_sections() -> None:
    assert "on_arm do" in FORMULA_TEMPLATE
    assert "on_intel do" not in FORMULA_TEMPLATE
    assert "agentrail --version" in FORMULA_TEMPLATE
    assert 'libexec.install "agentrail"' in FORMULA_TEMPLATE
    assert 'if (libexec/"agentrail").directory?' in FORMULA_TEMPLATE
    assert 'bin.install_symlink executable => "agentrail"' in FORMULA_TEMPLATE



def test_formula_render_can_be_formatted_to_path(tmp_path: Path) -> None:
    output = tmp_path / "agentrail.rb"
    output.write_text(
        FORMULA_TEMPLATE.format(
            version="0.1.4",
            owner_repo="Latentik/agentrail",
            arm_url="https://example.invalid/arm.tgz",
            arm_sha="a" * 64,
        ),
        encoding="utf-8",
    )
    rendered = output.read_text(encoding="utf-8")
    assert 'version "0.1.4"' in rendered
    assert 'homepage "https://github.com/Latentik/agentrail"' in rendered
