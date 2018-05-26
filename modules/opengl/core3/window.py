from OpenGL import GL
import rave.rendering


class Window(rave.rendering.Drawable):
    def __init__(self, parent, context):
        self.parent = parent
        self.context = context
        self.layers = []
        self.layer_names = {}

    def add_layer(self, layer):
        self.layers.append(layer)
        self.layer_names[layer.name] = layer

    def get_layer(self, name):
        return self.layer_names[name]

    def render(self, target):
        w, h = self.parent.render_size

        # Setup our rendering viewport.
        GL.glViewport(0, 0, w, h)
        # Basic black background.
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        for layer in self.layers:
            layer.render(target)

def create_gl_window(parent, context):
    return Window(parent, context)
