from solution import extract_ips

assert extract_ips("server at 192.168.1.10 and 10.0.0.255") == ["192.168.1.10", "10.0.0.255"]
assert extract_ips("bad 999.1.1.1 ok 8.8.8.8") == ["8.8.8.8"]
assert extract_ips("nothing here") == []
assert extract_ips("edge 255.255.255.255 and 0.0.0.0") == ["255.255.255.255", "0.0.0.0"]
print("OK")
