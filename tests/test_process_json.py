from clipfix.engines.detect_and_format import process_text

def test_json_pretty():
    ok, out, mode = process_text('{"a":1,"b":2}', allow_llm=False)
    assert ok
    assert '"a": 1' in out
