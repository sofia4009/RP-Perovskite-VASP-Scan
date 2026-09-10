from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_IDS = {
    "814",
    "2124",
}


def get_non_legacy_files():
    files = []

    for root in [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "tools",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "tests",
    ]:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            # Ignore Python bytecode and cache directories.
            if "__pycache__" in path.parts:
                continue

            if path.suffix in {
                ".pyc",
                ".pyo",
            }:
                continue

            files.append(path)

    return files


def test_forbidden_material_ids_not_in_non_legacy_code():
    files = get_non_legacy_files()

    for path in files:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        # Ignore this test's own literal definitions.
        if path.name == "test_search_outputs.py":
            continue

        for material_id in FORBIDDEN_IDS:
            assert material_id not in text, (
                f"Forbidden material ID {material_id} "
                f"found in non-legacy file: {path}"
            )


def test_gitignore_exists():
    gitignore = PROJECT_ROOT / ".gitignore"

    assert gitignore.exists(), (
        ".gitignore does not exist"
    )


def test_gitignore_contains_sensitive_patterns():
    gitignore = PROJECT_ROOT / ".gitignore"

    text = gitignore.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    required_patterns = [
        ".env",
        "__pycache__",
        "*.py[cod]",
    ]

    for pattern in required_patterns:
        assert pattern in text, (
            f"Expected pattern {pattern!r} "
            f"not found in .gitignore"
        )


if __name__ == "__main__":
    print("Running test_search_outputs.py directly...")

    test_forbidden_material_ids_not_in_non_legacy_code()
    test_gitignore_exists()
    test_gitignore_contains_sensitive_patterns()

    print("All direct tests passed.")
