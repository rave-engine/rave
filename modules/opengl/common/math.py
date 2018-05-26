import numpy

def ortho(left, right, top, bottom, far, near):
    rl = right - left
    tb = top - bottom
    fn = far - near
    return numpy.array([
         2 / rl, 0, 0, 0,
         0, 2 / tb, 0, 0,
         0, 0, -2 / fn,  0 ,
         - (right + left) / rl, - (top + bottom) / tb, - (far + near) / fn, 1
    ], dtype='float32')

def identity(n):
    return numpy.eye(n, dtype='float32')
