class Delegate(list):
    def __init__(self):
        super().__init__()

    def __call__(self, *args, **kwargs):
        for x in self:
            x(*args, **kwargs)

    def __iadd__(self, f):
        if callable(f):
            self.append(f)
        else:
            assert isinstance(f, list)
            assert all(callable(x) for x in f)
            self.extend(f)

        return self

    def __isub__(self, f):
        if callable(f):
            self.remove(f)
        else:
            assert isinstance(f, list)
            assert all(callable(x) for x in f)
            for x in f:
                self.remove(f)

        return self
