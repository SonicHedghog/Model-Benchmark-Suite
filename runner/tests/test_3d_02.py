from solution import rotate_z


def close(a, b):
    return all(abs(x - y) < 1e-6 for x, y in zip(a, b))


assert close(rotate_z((1, 0, 0), 90), (0, 1, 0))
assert close(rotate_z((0, 1, 5), 90), (-1, 0, 5))
assert close(rotate_z((1, 0, 0), 180), (-1, 0, 0))
assert close(rotate_z((3, 4, -2), 0), (3, 4, -2))
assert close(rotate_z((1, 1, 1), 360), (1, 1, 1))
print("OK")
