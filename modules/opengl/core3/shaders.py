from OpenGL import GL


class ShaderError(Exception):
    pass


class ShaderProgram:
    __slots__ = ('vertex', 'fragment', 'geometry', 'program', 'attribs')
    CACHE = {}

    def __new__(cls, vertex=None, fragment=None, geometry=None):
        if (vertex, fragment, geometry) in cls.CACHE:
            return cls.CACHE[vertex, fragment, geometry]

        instance = super().__new__(cls)
        cls.CACHE[vertex, fragment, geometry] = instance
        return instance

    def __del__(self):
        self.delete()

    def __init__(self, vertex=None, fragment=None, geometry=None):
        self.vertex = vertex
        self.fragment = fragment
        self.geometry = geometry
        self.program = None
        self.attribs = None

    def compile(self):
        vtid = fgid = gmid = None
        try:
            if self.vertex:
                vtid = self.compile_shader(self.vertex, GL.GL_VERTEX_SHADER)
            if self.fragment:
                fgid = self.compile_shader(self.fragment, GL.GL_FRAGMENT_SHADER)
            if self.geometry:
                gmid = self.compile_shader(self.geometry, GL.GL_GEOMETRY_SHADER)
        except:
            if vtid:
                GL.glDeleteShader(vtid)
            if fgid:
                GL.glDeleteShader(fgid)
            if gmid:
                GL.glDeleteShader(gmid)
            raise

        self.program = self.link(vtid, fgid, gmid)
        self.attribs = self.extract_attributes(self.program)

    def compile_shader(self, source, kind):
        shader = GL.glCreateShader(kind)
        GL.glShaderSource(shader, source)
        GL.glCompileShader(shader)

        if GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS) != GL.GL_TRUE:
            error = GL.glGetShaderInfoLog(shader).decode('utf-8')
            GL.glDeleteShader(shader)
            raise ShaderError(error)

        return shader

    def link(self, vertex, fragment, geometry):
        program = GL.glCreateProgram()
        if vertex:
            GL.glAttachShader(program, vertex)
        if fragment:
            GL.glAttachShader(program, fragment)
        if geometry:
            GL.glAttachShader(program, geometry)
        GL.glLinkProgram(program)

        status = GL.glGetProgramiv(program, GL.GL_LINK_STATUS)

        if vertex:
            GL.glDetachShader(program, vertex)
            GL.glDeleteShader(vertex)
        if fragment:
            GL.glDetachShader(program, fragment)
            GL.glDeleteShader(fragment)
        if geometry:
            GL.glDetachShader(program, geometry)
            GL.glDeleteShader(geometry)

        if status != GL.GL_TRUE:
            error = GL.glGetProgramInfoLog(program).decode('utf-8')
            GL.glDeleteProgram(program)
            raise ShaderError(error)

        return program

    def extract_attributes(self, program):
        attribs = {}
        count = GL.glGetProgramiv(program, GL.GL_ACTIVE_ATTRIBUTES)

        bufsize = 64
        buf = (GL.GLchar * bufsize)()
        namesize = GL.GLsizei()
        size = GL.GLint()
        kind = GL.GLenum()

        for i in range(count):
            GL.glGetActiveAttrib(program, i, bufsize, namesize, size, kind, buf)
            name = buf.value.decode('utf-8')
            idx = GL.glGetAttribLocation(program, name)
            attribs[name] = idx

        count = GL.glGetProgramiv(program, GL.GL_ACTIVE_UNIFORMS)

        for i in range(count):
            name, size, kind = GL.glGetActiveUniform(program, i)
            name = name.decode('utf-8')
            idx = GL.glGetUniformLocation(program, name)
            attribs[name] = idx

        return attribs

    def delete(self):
        if self.program:
            GL.glDeleteProgram(self.program)

    def use(self):
        if not self.program:
            raise ValueError('No program. Did you forget to compile()?')
        GL.glUseProgram(self.program)

    def get_index(self, attribute):
        return self.attribs[attribute]
