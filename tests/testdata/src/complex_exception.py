def f():
    l = []
    try:
        with __any_object__:
            l.append("w")
            raise ValueError("oops")
            l.append("z")
        l.append("e")
    except ValueError as e:
        assert str(e) == "oops"
        l.append("x")
    l.append("r")
    s = "".join(l)
    return s
