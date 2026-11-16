from tools.letter_checks import check_letter, count_words, load_banned_phrases

BODY = "woord " * 300


def test_valid_letter_passes():
    report = check_letter(f"Ik ben Tim, 23 jaar. {BODY}", banned_phrases=[], age=23)
    assert report.passed
    assert report.placeholders == []


def test_length_boundaries():
    assert check_letter("woord " * 250, [], None).length_ok
    assert not check_letter("woord " * 249, [], None).length_ok
    assert check_letter("woord " * 400, [], None).length_ok
    assert not check_letter("woord " * 401, [], None).length_ok


def test_known_typo_is_flagged():
    report = check_letter(f"Mijn hard sneller kloppen. {BODY}", [], None)
    assert report.typos == ["hard sneller -> hart sneller"]
    assert not report.passed


def test_wrong_age_is_flagged():
    report = check_letter(f"Ik ben 24 jaar. {BODY}", [], age=23)
    assert report.wrong_age
    assert not report.passed


def test_banned_phrase_is_case_insensitive():
    report = check_letter(f"Ik ben De Perfecte Fit. {BODY}", ["de perfecte fit"], None)
    assert report.banned_phrases == ["de perfecte fit"]


def test_placeholders_are_reported_but_do_not_fail():
    report = check_letter(f"Telefoon: [telefoon] {BODY}", [], None)
    assert report.placeholders == ["[telefoon]"]
    assert report.passed


def test_count_words_handles_punctuation():
    assert count_words("Hallo, ik ben Tim-Aarts!") == 4


def test_load_banned_phrases_reads_only_its_section(tmp_path):
    guide = tmp_path / "style.md"
    guide.write_text("## Rules\n- not this\n## Banned phrases\n- \"de perfecte fit\"\n- passie\n## Other\n- nope\n")
    assert load_banned_phrases(guide) == ["de perfecte fit", "passie"]
