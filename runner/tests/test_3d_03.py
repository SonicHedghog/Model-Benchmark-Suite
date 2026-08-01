from solution import ray_hits_sphere

# straight at the sphere
assert ray_hits_sphere((0, 0, 0), (1, 0, 0), (5, 0, 0), 1) is True
# pointing away (sphere behind origin)
assert ray_hits_sphere((0, 0, 0), (-1, 0, 0), (5, 0, 0), 1) is False
# misses to the side
assert ray_hits_sphere((0, 0, 0), (1, 0, 0), (5, 3, 0), 1) is False
# grazing tangent
assert ray_hits_sphere((0, 0, 0), (1, 0, 0), (5, 1, 0), 1) is True
# origin inside sphere
assert ray_hits_sphere((5, 0, 0), (0, 1, 0), (5, 0, 0), 2) is True
# unnormalized direction
assert ray_hits_sphere((0, 0, 0), (10, 0, 0), (5, 0, 0), 1) is True
print("OK")
