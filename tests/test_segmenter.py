from clipfix.engines.segmenter import regex_segment

def test_heredoc_detect():
    text = "PYTHONPATH=. python - <<'PY'\nprint('x')\nPY"
    segs = regex_segment(text)
    assert len(segs) == 1
    assert segs[0].kind == "bash_python_heredoc"
    assert segs[0].inner_kind == "python"
