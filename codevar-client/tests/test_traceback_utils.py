from codevar_client.traceback_utils import extract_exception_info


def _raise_value_error():
    raise ValueError("boom")


def test_extracts_exception_type_and_message_frame():
    try:
        _raise_value_error()
    except ValueError as exc:
        info = extract_exception_info(exc)

    assert info.exception_type == "ValueError"
    assert info.file_path.endswith("test_traceback_utils.py")
    assert info.line_number > 0
    assert "ValueError: boom" in info.stack_trace


def test_uses_the_innermost_frame_for_nested_calls():
    def inner():
        raise KeyError("missing")

    def outer():
        inner()

    try:
        outer()
    except KeyError as exc:
        info = extract_exception_info(exc)

    assert info.exception_type == "KeyError"
    assert info.file_path.endswith("test_traceback_utils.py")
