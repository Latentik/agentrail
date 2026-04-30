from scripts.release_metadata import tag_to_version, verify_tag


def test_tag_to_version_parses_semver_tag() -> None:
    assert tag_to_version("v0.1.5") == "0.1.5"



def test_verify_tag_accepts_matching_project_version() -> None:
    verify_tag("v0.1.8")
