from solution import run_length_encode

assert run_length_encode("aaabccdddd") == "a3b1c2d4"
assert run_length_encode("") == ""
assert run_length_encode("a") == "a1"
assert run_length_encode("abc") == "a1b1c1"
assert run_length_encode("zzzzzzzzzzzz") == "z12"
print("OK")
