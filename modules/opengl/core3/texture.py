from OpenGL import GL
import numpy
import ctypes

from . import shaders


class Texture:
    __slots__ = ('width', 'height', 'data', 'texture')

    def __init__(self, width, height, data):
        self.width = width
        self.height = height
        self.data = data
        self.texture = GL.glGenTextures(1)

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, self.width, self.height, 0, GL.GL_BGRA, GL.GL_UNSIGNED_INT_8_8_8_8, ctypes.cast(self.data, ctypes.c_void_p))
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def bind(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

    def unbind(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

class Image:
    FRAGMENT = """
    #version 330 core
    in vec2 v_texcoord;
    out vec4 o_color;

    uniform sampler2D u_tex;

    void main(void) {
        o_color = texture(u_tex, v_texcoord);
    }
    """.strip()
    VERTEX = """
    #version 330 core
        in vec2 a_vertex;
    in vec2 a_texcoord;
    out vec2 v_texcoord;

    void main(void) {
        gl_Position = vec4(a_vertex, 0.0, 1.0);
        v_texcoord = a_texcoord;
        v_texcoord.y = -v_texcoord.y;
    }""".strip()

    def __init__(self, tex):
        self.vertexes = numpy.array([
            1000.0     , -1800.0,
            -1000.0  , -1800.0,
            1000.0     , 1800.0,

            -1000.0     ,1800.0,
            -1000.0  , -1800.0,
            1000.0     , 1800.0,
        ], dtype='float32')

        self.texcoords = numpy.array([
            1280.0     , -720.0,
            -1280.0  , -720.0,
            1280.0     , 720.0,

            -1280.0     , 720.0,
            -1280.0  , -720.0,
            1280.0     , 720.0,
        ], dtype='float32')
        self.tex = tex
        self.program = shaders.ShaderProgram(fragment=self.FRAGMENT, vertex=self.VERTEX)
        self.program.compile()

        self.vao = GL.glGenVertexArrays(1)
        self.vertex_vbo, self.texcoords_vbo = GL.glGenBuffers(2)

        self.program.use()
        GL.glBindVertexArray(self.vao)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vertex_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, len(self.vertexes) * 2 * 4, self.vertexes, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(self.program.get_index('a_vertex'))
        GL.glVertexAttribPointer(self.program.get_index('a_vertex'), 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.texcoords_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, len(self.texcoords) * 2 * 4, self.texcoords, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(self.program.get_index('a_texcoord'))
        GL.glVertexAttribPointer(self.program.get_index('a_texcoord'), 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

        GL.glBindVertexArray(0)

    def render(self, target):
        self.program.use()
        self.tex.bind()
        GL.glEnable(GL.GL_BLEND);
        GL.glBlendFunc(GL.GL_SRC_ALPHA,GL.GL_ONE_MINUS_SRC_ALPHA);
        GL.glUniform1i(self.program.get_index('u_tex'), 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex.texture)
        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        #GL.glBindVertexArray(0)
        #GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
