import pytest
from PIL import ImageFont
from src.image_manager import MockImageManager

class TestMockImageManager:
    @pytest.fixture
    def manager(self):
        return MockImageManager()

    @pytest.fixture
    def font(self):
        try:
            return ImageFont.load_default()
        except IOError:
            pytest.skip("Default font not available")

    def test_wrap_text_basic(self, manager, font):
        text = "Hello world"
        max_width = 1000
        lines = manager._wrap_text(text, font, max_width)
        assert lines == ["Hello world"]

    def test_wrap_text_splitting(self, manager, font):
        # Measure width of 'A'
        bbox = font.getbbox("A")
        width_a = bbox[2] - bbox[0]

        # Construct text: "AAAAA AAAAA"
        text = "A" * 5 + " " + "A" * 5

        # Limit width so only 5 As fit.
        # width_a * 5 is the width of "AAAAA".
        # Plus space width.
        # If we set max_width to slightly more than 5 As, the second word shouldn't fit if we account for space + second word.

        # Let's rely on a tighter constraint.
        bbox_block = font.getbbox("A" * 5)
        width_block = bbox_block[2] - bbox_block[0]

        # Max width is exactly one block.
        # The space + next block will exceed this.
        max_width = width_block + 1

        lines = manager._wrap_text(text, font, max_width)

        # Should be two lines
        assert len(lines) == 2
        assert lines[0] == "A" * 5
        assert lines[1] == "A" * 5

    def test_wrap_text_long_word(self, manager, font):
        # A word longer than max_width should generally be on its own line
        bbox = font.getbbox("A")
        width_a = bbox[2] - bbox[0]

        text = "A" * 10
        max_width = width_a * 5

        lines = manager._wrap_text(text, font, max_width)
        assert len(lines) == 1
        assert lines[0] == text

    def test_wrap_text_empty(self, manager, font):
        lines = manager._wrap_text("", font, 100)
        assert lines == []
