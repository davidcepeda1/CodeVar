from app.fingerprint import compute_fingerprint


def test_same_inputs_produce_same_fingerprint():
    a = compute_fingerprint("ValueError", "app/foo.py", 10)
    b = compute_fingerprint("ValueError", "app/foo.py", 10)
    assert a == b


def test_different_exception_type_changes_fingerprint():
    a = compute_fingerprint("ValueError", "app/foo.py", 10)
    b = compute_fingerprint("KeyError", "app/foo.py", 10)
    assert a != b


def test_different_line_number_changes_fingerprint():
    a = compute_fingerprint("ValueError", "app/foo.py", 10)
    b = compute_fingerprint("ValueError", "app/foo.py", 11)
    assert a != b


def test_different_file_path_changes_fingerprint():
    a = compute_fingerprint("ValueError", "app/foo.py", 10)
    b = compute_fingerprint("ValueError", "app/bar.py", 10)
    assert a != b
