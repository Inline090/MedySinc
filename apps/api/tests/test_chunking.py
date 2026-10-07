from app.ai.chunking import MAX_TOKENS, chunk_text, estimate_tokens, split_sentences


def test_estimate_tokens_uses_four_characters_per_token():
    """Checks that the token estimate rule of thumb (4 chars = 1 token) works."""
    assert estimate_tokens("abcdefgh") == 2
    assert estimate_tokens("") == 1


def test_split_sentences_breaks_on_sentence_punctuation():
    """Checks that sentences are split correctly on '.', '!', and '?'."""
    assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]


def test_split_sentences_returns_nothing_for_blank_input():
    """Checks that empty strings return empty lists instead of blank sentences."""
    assert split_sentences("") == []
    assert split_sentences("   \n\t ") == []


def test_chunk_text_returns_nothing_for_blank_input():
    """Checks that chunking empty text returns an empty list."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_keeps_short_text_in_a_single_chunk():
    """Checks that a single sentence isn't split into multiple chunks."""
    chunks = chunk_text("The patient was prescribed Dolo 650 for fever.")

    assert len(chunks) == 1
    assert chunks[0].index == 0


def test_chunk_text_splits_long_input_and_numbers_the_chunks():
    """Checks that long text is split into sequentially numbered chunks."""
    text = " ".join(f"Sentence number {index}." for index in range(600))

    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_no_chunk_exceeds_the_token_budget():
    """Checks that no chunk goes over the maximum token limit."""
    text = " ".join(f"Sentence number {index}." for index in range(600))

    for chunk in chunk_text(text):
        assert chunk.token_count <= MAX_TOKENS


def test_consecutive_chunks_overlap_so_a_finding_survives_the_boundary():
    """Checks that chunks overlap to keep context across boundaries."""
    text = " ".join(f"Sentence number {index}." for index in range(600))
    chunks = chunk_text(text)

    assert len(chunks) >= 2

    opening = " ".join(chunks[1].content.split()[:4])

    assert opening in chunks[0].content


def test_an_oversized_sentence_without_punctuation_is_split_by_words():
    """Checks that a very long sentence without punctuation is split by words."""
    text = " ".join(["word"] * 5000)

    chunks = chunk_text(text)

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.token_count <= MAX_TOKENS
