"""
rave rendering primitives.
"""


## Base classes.

class Renderable:
    """ Something that can be rendered. """
    def render(self, target):
        pass


class Drawable(Renderable):
    """ Something that can be rendered visually. """
    pass


class Soundable(Renderable):
    """ Something that can be rendered aurally. """
    pass



## Visual rendering.

class Layer(Drawable):
    """ A layer of drawables within a window. """
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def render(self, target):
        for child in self.children:
            child.render(target)

class PixelFormat:
    """ Image pixel format. """
    __slots__ = (
        'r_bits', 'g_bits', 'b_bits', 'a_bits',
        'type', 'order',
        'r_mask', 'g_mask', 'b_mask', 'a_mask',
        'r_shift', 'g_shift', 'b_shift', 'a_shift'
    )
    TYPE_ARRAY  = 1
    TYPE_PACKED = 2

    def __init__(self, **kwargs):
        self.r_bits  = kwargs.get('r_bits', 8)
        self.g_bits  = kwargs.get('g_bits', 8)
        self.b_bits  = kwargs.get('b_bits', 8)
        self.a_bits  = kwargs.get('a_bits', 8)
        self.type    = kwargs.get('type', self.TYPE_PACKED)
        self.order   = kwargs.get('order', [ 'b', 'g', 'r', 'a' ])
        self.r_mask  = kwargs.get('r_mask', 0x0000FF00)
        self.g_mask  = kwargs.get('g_mask', 0x00FF0000)
        self.b_mask  = kwargs.get('b_mask', 0xFF000000)
        self.a_mask  = kwargs.get('a_mask', 0x000000FF)
        self.r_shift = kwargs.get('r_shift', 8)
        self.g_shift = kwargs.get('g_shift', 16)
        self.b_shift = kwargs.get('b_shift', 24)
        self.a_shift = kwargs.get('a_shift', 0)

# Some standard formats.
PixelFormat.FORMAT_RGB565   = PixelFormat(r_bits=5, g_bits=6, b_bits=5, a_bits=0, type=PixelFormat.TYPE_PACKED, r_mask=0xF800, g_mask=0x07E0, b_mask=0x1F, r_shift=11, g_shift=5, b_shift=0)
PixelFormat.FORMAT_RGBA8888 = PixelFormat(type=PixelFormat.TYPE_ARRAY, order=['r', 'g', 'b', 'a'])
PixelFormat.FORMAT_ABGR8888 = PixelFormat(type=PixelFormat.TYPE_ARRAY, order=['a', 'b', 'g', 'r'])
PixelFormat.FORMAT_BGRA8888 = PixelFormat(type=PixelFormat.TYPE_ARRAY, order=['b', 'g', 'r', 'a'])
PixelFormat.FORMAT_ARGB8888 = PixelFormat(type=PixelFormat.TYPE_ARRAY, order=['a', 'r', 'g', 'b'])
