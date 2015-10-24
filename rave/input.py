"""
rave input primitives.
"""
import collections
import rave.common


## Key definitions. Sigh.
class Key(rave.common.IncrementingEnum):
    """ Common keyboard keys. """

    # Alpha.
    A = ()
    B = ()
    C = ()
    D = ()
    E = ()
    F = ()
    G = ()
    H = ()
    I = ()
    J = ()
    K = ()
    L = ()
    M = ()
    N = ()
    O = ()
    P = ()
    Q = ()
    R = ()
    S = ()
    T = ()
    U = ()
    V = ()
    W = ()
    X = ()
    Y = ()
    Z = ()

    # Numeric.
    _1 = ()
    _2 = ()
    _3 = ()
    _4 = ()
    _5 = ()
    _6 = ()
    _7 = ()
    _8 = ()
    _9 = ()
    _0 = ()

    # Special.
    SPACE = ()         #  
    EXCLAMATION = ()   # !
    AT = ()            # @
    HASH = ()          # #
    DOLLAR = ()        # $
    PERCENT = ()       # %
    CARET = ()         # ^
    AMPERSAND = ()     # &
    ASTERISK = ()      # *
    LEFT_PAREN = ()    # (
    RIGHT_PAREN = ()   # )
    DASH = ()          # -
    UNDERSCORE = ()    # _
    PLUS = ()          # +
    EQUAL = ()         # =
    LEFT_BRACKET = ()  # [
    RIGHT_BRACKET = () # ]
    LEFT_BRACE = ()    # {
    RIGHT_BRACE = ()   # }
    COLON = ()         # :
    SEMICOLON = ()     # ;
    QUOTE = ()         # '
    DOUBLE_QUOTE = ()  # "
    SLASH = ()         # /
    BACKSLASH = ()     # \
    PIPE = ()          # |
    LESS = ()          # <
    MORE = ()          # >
    PERIOD = ()        # .
    COMMA = ()         # ,
    QUESTION = ()      # ?
    GRAVE = ()         # `
    TILDE = ()         # ~
    PLUSMINUS = ()     # ±
    SECTION = ()       # §

    # Function.
    F1  = ()
    F2  = ()
    F3  = ()
    F4  = ()
    F5  = ()
    F6  = ()
    F7  = ()
    F8  = ()
    F9  = ()
    F10 = ()
    F11 = ()
    F12 = ()
    F13 = ()
    F14 = ()
    F15 = ()
    F16 = ()
    F17 = ()
    F18 = ()
    F19 = ()
    F20 = ()
    F21 = ()
    F22 = ()
    F23 = ()
    F24 = ()

    # Control.
    ESCAPE = ()
    SHIFT = ()
    LEFT_SHIFT = ()
    RIGHT_SHIFT = ()
    TAB = ()

    CONTROL = ()
    LEFT_CONTROL = ()
    RIGHT_CONTROL = ()
    ALT = ()
    LEFT_ALT = ()
    RIGHT_ALT = ()
    META = ()
    LEFT_META = ()
    RIGHT_META = ()
    FUNCTION = ()
    MENU = ()

    CAPS_LOCK = ()
    NUM_LOCK = ()
    SCROLL_LOCK = ()
    PRINT_SCREEN = ()

    HOME = ()
    END = ()
    INSERT = ()
    DELETE = ()
    PAGE_UP = ()
    PAGE_DOWN = ()
    PAUSE = ()

    LEFT_ARROW = ()
    RIGHT_ARROW = ()
    UP_ARROW = ()
    DOWN_ARROW = ()

    BACKSPACE = ()
    ENTER = ()

    # Media. What do we even do with them?
    BRIGHTNESS_DOWN = ()
    BRIGHTNESS_UP = ()
    VOLUME_DOWN = ()
    VOLUME_UP = ()
    VOLUME_MUTE = ()
    MEDIA_PLAY = ()
    MEDIA_STOP = ()
    MEDIA_PREVIOUS = ()
    MEDIA_NEXT = ()
    MEDIA_EJECT = ()

    # Obscure misc keys.
    INTERNET = ()
    CALCULATOR = ()
    COMPUTER = ()
    POWER = ()

    # Keypad.
    KEYPAD_0 = ()
    KEYPAD_1 = ()
    KEYPAD_2 = ()
    KEYPAD_3 = ()
    KEYPAD_4 = ()
    KEYPAD_5 = ()
    KEYPAD_6 = ()
    KEYPAD_7 = ()
    KEYPAD_8 = ()
    KEYPAD_9 = ()
    KEYPAD_INSERT = ()
    KEYPAD_DELETE = ()
    KEYPAD_ENTER = ()
    KEYPAD_HOME = ()
    KEYPAD_END = ()
    KEYPAD_SLASH = ()
    KEYPAD_ASTERISK = ()
    KEYPAD_DASH = ()
    KEYPAD_PLUS = ()
    KEYPAD_PAGE_UP = ()
    KEYPAD_PAGE_DOWN = ()

    OTHER = ()


class MouseButton(rave.common.IncrementingEnum):
    """ Common mouse buttons. """
    LEFT = ()
    MIDDLE = ()
    RIGHT = ()
    SCROLL = ()
    OTHER = ()


class ControllerButton(rave.common.IncrementingEnum):
    """ Common controller buttons. """
    HOME = ()
    START = ()
    BACK = ()

    LEFT_STICK = ()
    RIGHT_STICK = ()

    LEFT_SHOULDER = ()
    RIGHT_SHOULDER = ()
    LEFT_TRIGGER = ()
    RIGHT_TRIGGER = ()

    DIRECTION_UP = ()
    DIRECTION_DOWN = ()
    DIRECTION_LEFT = ()
    DIRECTION_RIGHT = ()

    OTHER = ()


class Gesture(rave.common.IncrementingEnum):
    """ Common gestures. """
    TAP = ()      # (fingers, amount)
    PRESS = ()    # fingers
    SCROLL = ()   # (fingers, direction, amount)
    PAN = ()      # (fingers, angle, amount)
    FLICK = ()    # (fingers, direction)
    PINCH = ()    # amount
    ZOOM = ()     # amount
    ROTATE = ()   # amount
    OTHER = ()    # (id, args)


class Dispatcher:
    """ Keep track of input state and dispatch to contexts. """
    def __init__(self, bus):
        self.contexts = collections.OrderedDict()
        self.input_state = frozenset()
        self.bus = bus

        # Caching.
        self.cache_inputs = True
        self._cached_additions = set()
        self._cached_removals = set()


    ## Hooks.

    def register_hooks(self):
        """ Hook events from native input layer. """
        self.bus.hook('input.keyboard.press', self.on_keyboard_key)
        self.bus.hook('input.keyboard.repeat', self.on_keyboard_key)
        self.bus.hook('input.keyboard.release', self.on_keyboard_key)
        self.bus.hook('input.mouse.press', self.on_mouse_button)
        self.bus.hook('input.mouse.release', self.on_mouse_button)
        self.bus.hook('input.mouse.move', self.on_mouse_move)
        self.bus.hook('input.mouse.scroll', self.on_mouse_scroll)
        self.bus.hook('input.controller.press', self.on_controller_button)
        self.bus.hook('input.controller.release', self.on_controller_button)
        self.bus.hook('input.dispatch', self.cached_dispatch)

    def on_keyboard_key(self, event, sym, nativesym):
        sym = nativesym if sym == Key.OTHER else sym
        if event.endswith('.press'):
            self._add_button(sym)
        else:
            self._remove_button(sym)

    def on_mouse_button(self, event, mouse, sym, nativesym, clicks, pos):
        sym = (nativesym, clicks) if sym == MouseButton.OTHER else (sym, clicks)
        if event.endswith('.press'):
            self._add_button(sym)
        else:
            self._remove_button(sym)

    def on_mouse_move(self, event, mouse, pos, relpos):
        pass

    def on_mouse_scroll(self, event, mouse, relpos):
        pass

    def on_controller_button(self, event, sym, nativesym):
        sym = nativesym if sym == ControllerButton.OTHER else sym
        if event.endswith('.press'):
            self._add_button(sym)
        else:
            self._remove_button(sym)


    ## Internal APIs.

    def _add_button(self, sym):
        if self.cache_inputs:
            self._cached_removals.discard(sym)
            self._cached_additions.add(sym)
        else:
            self.input_state.add(sym)
            self.dispatch()

    def _remove_button(self, sym):
        if self.cache_inputs:
            self._cached_additions.discard(sym)
            self._cached_removals.add(sym)
        else:
            self.input_state.discard(sym)
            self.dispatch()


    ## Dispatching.

    def cached_dispatch(self, event):
        if not self.cache_inputs:
            return

        if self._cached_additions:
            self.input_state |= self._cached_additions
            self._cached_additions = set()
        if self._cached_removals:
            self.input_state -= self._cached_removals
            self._cached_removals = set()
        self.dispatch()

    def dispatch(self):
        for context in reversed(list(self.contexts.values())):
            if context.handle(self.input_state, self.bus):
                break


    ## Public API.

    def push_context(self, ctx):
        self.contexts[ctx.name] = ctx

    def pop_context(self, name):
        return self.contexts.pop(name)

    def add_bind(self, name, bind, event):
        self.contexts[name].add_bind(bind, event)

    def remove_bind(self, name, bind, event):
        self.contexts[name].remove_bind(bind, event)



class Context:
    def __init__(self, name, delegate=True):
        self.name = name
        self.actions = {}
        self.cached_actions = {}
        self.delegate = delegate

    def handle(self, state, bus):
        if state not in self.cached_actions:
            actions = []
            for bind, event in self.actions.items():
                if bind.issubset(state):
                    actions.append(event)
            self.cached_actions[state] = actions
        else:
            actions = self.cached_actions[state]

        for action in actions:
            bus.emit(action, state)

        if actions:
            return True
        else:
            return not self.delegate

    def add_bind(self, bind, event):
        self.actions[frozenset(bind)] = event

    def remove_bind(self, bind, event):
        self.actions[frozenset(bind)].remove(event)


