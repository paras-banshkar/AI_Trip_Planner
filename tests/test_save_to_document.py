"""
Unit tests for utils/save_to_document.py.

Run:
    pytest tests/test_save_to_document.py -v
"""
import os
import glob
from utils.save_to_document import save_document


class TestSaveDocument:
    def test_creates_directory_if_missing(self, tmp_path):
        out_dir = tmp_path / "does_not_exist_yet"
        assert not out_dir.exists()

        save_document("Day 1: Arrive in Goa.", directory=str(out_dir))

        assert out_dir.exists()

    def test_returns_path_to_written_file(self, tmp_path):
        result_path = save_document("Day 1: Arrive in Goa.", directory=str(tmp_path))

        assert result_path is not None
        assert os.path.exists(result_path)

    def test_file_contains_the_response_text(self, tmp_path):
        result_path = save_document("Unique itinerary text 12345", directory=str(tmp_path))

        with open(result_path, encoding="utf-8") as f:
            content = f.read()
        assert "Unique itinerary text 12345" in content

    def test_filename_is_timestamped_markdown(self, tmp_path):
        result_path = save_document("content", directory=str(tmp_path))

        assert result_path.endswith(".md")
        assert "AI_Trip_Planner_" in os.path.basename(result_path)

    def test_handles_unicode_content_without_crashing(self, tmp_path):
        # Regression-style guard: this module already opens with
        # encoding="utf-8" explicitly, so ₹ and other non-ASCII characters
        # in the itinerary must not raise (see the same class of bug fixed
        # in eval/tool_call_accuracy.py and notebook/benchmark.py).
        result_path = save_document("Total budget: ₹45,000", directory=str(tmp_path))

        with open(result_path, encoding="utf-8") as f:
            content = f.read()
        assert "₹45,000" in content
