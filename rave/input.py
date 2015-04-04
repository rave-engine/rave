"""
rave input primitives.
"""
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
