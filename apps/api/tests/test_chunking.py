from app.ai.chunking import MAX_TOKENS, chunk_text, estimate_tokens, split_sentences
from app.ai.extraction import extract_text, needs_ocr


def test_estimate_tokens_uses_four_characters_per_token():
    assert estimate_tokens("abcdefgh") == 2
    assert estimate_tokens("") == 1


def test_split_sentences_breaks_on_sentence_punctuation():
    assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]


def test_split_sentences_returns_nothing_for_blank_input():
    assert split_sentences("") == []
    assert split_sentences("   \n\t ") == []


def test_chunk_text_returns_nothing_for_blank_input():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_keeps_short_text_in_a_single_chunk():
    chunks = chunk_text("The patient was prescribed Dolo 650 for fever.")

    assert len(chunks) == 1
    assert chunks[0].index == 0


def test_chunk_text_splits_long_input_and_numbers_the_chunks():
    text = " ".join(f"Sentence number {index}." for index in range(600))

    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_no_chunk_exceeds_the_token_budget():
    text = " ".join(f"Sentence number {index}." for index in range(600))

    for chunk in chunk_text(text):
        assert chunk.token_count <= MAX_TOKENS


def test_consecutive_chunks_overlap_so_a_finding_survives_the_boundary():
    text = " ".join(f"Sentence number {index}." for index in range(600))
    chunks = chunk_text(text)

    assert len(chunks) >= 2

    opening = " ".join(chunks[1].content.split()[:4])

    assert opening in chunks[0].content


def test_an_oversized_sentence_without_punctuation_is_split_by_words():
    text = " ".join(["word"] * 5000)

    chunks = chunk_text(text)

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.token_count <= MAX_TOKENS


def test_extract_text_returns_nothing_for_images_because_there_is_no_ocr():
    assert extract_text(b"\x89PNG\r\n\x1a\n", "image/png") == ""


def test_needs_ocr_flags_text_that_is_too_short_to_use():
    assert needs_ocr("") is True
    assert needs_ocr("too short") is True
    assert needs_ocr("x" * 60) is False
