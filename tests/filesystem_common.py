from functools import wraps
from rave import filesystem as fs

class DummyProvider:
    """ Simple dummy provider that only provides a single file: foo.txt """

    def list(self):
        return [ '/foo.txt' ]

    def has(self, filename):
        return filename in self.list()

    def open(self, filename):
        if not self.has(filename):
            raise fs.FileNotFound(filename)

        return DummyFile(self, filename)

class DummyFile(fs.File):
    """ Simple dummy file with no real backend and initial content of 'this is a test file.' """
    ERROR = False

    def __init__(self, provider, filename):
        self.provider = provider
        self.contents = b'this is a test file.'
        if self.ERROR:
            raise fs.AccessDenied()

    def read(self, amount=None):
        if not self.opened():
            raise fs.FileClosed(self.filename)

        if amount is None:
            amount = len(self.contents)

        data = self.contents[:amount]
        self.contents = self.contents[amount:]
        return data

    def write(self, data):
        if not self.opened():
            raise fs.FileClosed(self.filename)
        self.contents += data

    def opened(self):
        return self.contents is not None

    def close(self):
        self.contents = None


class DummyTransformer:
    """ A simple dummy transformer that transforms .txt files into .rot13.txt files. """
    CONSUMES = False
    RELATIVE = True

    def __init__(self, filename):
        self.origfile = filename
        self.file = fs.normalize(fs.basename(filename.replace('.txt', '.rot13.txt')))

    @classmethod
    def consumes(cls):
        return cls.CONSUMES

    @classmethod
    def relative(cls):
        return cls.RELATIVE

    def valid(self):
        return not self.origfile.endswith('.rot13.txt')

    def list(self):
        return [ self.file ]

    def has(self, filename):
        return filename in self.list()

    def open(self, filename):
        if not self.has(filename):
            raise fs.FileNotFound(filename)

        return ROT13File(fs.open(self.origfile))

class ROT13File(fs.File):
    """ ROT13 stream. """

    def __init__(self, parent):
        import codecs
        self.parent = parent
        self.enc = codecs.getencoder('rot-13')
        self.dec = codecs.getdecoder('rot-13')

    def close(self):
        self.parent.close()

    def opened(self):
        return self.parent.opened()

    def readable(self):
        return self.parent.readable()

    def writable(self):
        return self.parent.writable()

    def seekable(self):
        return self.parent.seekable()

    def read(self, amount=None):
        data = self.parent.read(amount).decode('utf-8')
        return self.enc(data)[0]

    def write(self, data):
        self.parent.write(self.dec(data)[0].encode('utf-8'))

class DummyOnDemand:
    """ A dummy on demand provider that will serve on-demand:// and return a DummyFile for every file ending in .txt. """

    def has(self, filename):
        return filename.endswith('.txt')

    def open(self, filename):
        if not self.has(filename):
            raise fs.FileNotFound(filename)
        return DummyFile(self, filename)


def dummysetup(f):
    """ Simple setup that provides the test function with a dummy provider. """
    @wraps(f)
    def setup():
        provider = DummyProvider()
        fs.clear()
        fs.mount('/', provider)

        f(provider=provider)

    return setup

def dummytransformsetup(f):
    """ Simple setup that provides the test function with a dummy provider and transformer. """
    @wraps(f)
    def setup():
        provider = DummyProvider()
        fs.clear()
        fs.mount('/', provider)
        fs.transform('.txt$', DummyTransformer)

        f(provider=provider)

    return setup

def dummyondemandsetup(f):
    """ Simple setup that provides the test functiion with an on-demand provider. """
    @wraps(f)
    def setup():
        ondemand = DummyOnDemand()
        fs.clear()
        fs.add_on_demand('on-demand://', ondemand)

        f(ondemand=ondemand)

    return setup