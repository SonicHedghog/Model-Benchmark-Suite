from solution import min_coins

assert min_coins(11, [1, 2, 5]) == 3
assert min_coins(0, [1, 2, 5]) == 0
assert min_coins(3, [2]) == -1
assert min_coins(6, [1, 3, 4]) == 2
assert min_coins(10000, [7, 13, 29]) > 0  # must finish fast
print("OK")
