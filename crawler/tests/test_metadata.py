from pathlib import Path

import pytest
import yaml


def test_metadata_in_saved_files():
    # Only run this test if the crawler has run and generated files
    storage_dir = Path("data_sources/django2-orm-cookbook")
    if not storage_dir.exists():
        pytest.skip("Storage directory does not exist yet. Run the crawler first.")

    md_files = list(storage_dir.rglob("*.md"))
    if not md_files:
        pytest.skip("No markdown files found to verify.")

    for file_path in md_files:
        content = file_path.read_text(encoding="utf-8")

        # Verify it starts with YAML front matter
        assert content.startswith("---\n"), f"File {file_path} doesn't start with YAML Front Matter"

        # Extract YAML front matter
        end_idx = content.find("---\n", 4)
        assert end_idx != -1, f"File {file_path} is missing closing --- for Front Matter"

        yaml_content = content[4:end_idx]
        metadata = yaml.safe_load(yaml_content)

        # Verify essential keys
        assert "source_url" in metadata
        assert "target_version" in metadata
        assert metadata["target_version"] == "2.x"
        assert "collected_at" in metadata
