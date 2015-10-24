from sdl2 import *
import rave.events
from rave.input import Key


KEY_MAPPING = {
    SDLK_a: Key.A,
    SDLK_b: Key.B,
    SDLK_c: Key.C,
    SDLK_d: Key.D,
    SDLK_e: Key.E,
    SDLK_f: Key.F,
    SDLK_g: Key.G,
    SDLK_h: Key.H,
    SDLK_i: Key.I,
    SDLK_j: Key.J,
    SDLK_k: Key.K,
    SDLK_l: Key.L,
    SDLK_m: Key.M,
    SDLK_n: Key.N,
    SDLK_o: Key.O,
    SDLK_p: Key.P,
    SDLK_q: Key.Q,
    SDLK_r: Key.R,
    SDLK_s: Key.S,
    SDLK_t: Key.T,
    SDLK_u: Key.U,
    SDLK_v: Key.V,
    SDLK_w: Key.W,
    SDLK_x: Key.X,
    SDLK_y: Key.Y,
    SDLK_z: Key.Z,

    SDLK_0: Key._0,
    SDLK_1: Key._1,
    SDLK_2: Key._2,
    SDLK_3: Key._3,
    SDLK_4: Key._4,
    SDLK_5: Key._5,
    SDLK_6: Key._6,
    SDLK_7: Key._7,
    SDLK_8: Key._8,
    SDLK_9: Key._9,

    SDLK_SPACE:        Key.SPACE,
    SDLK_EXCLAIM:      Key.EXCLAMATION,
    SDLK_AT:           Key.AT,
    SDLK_HASH:         Key.HASH,
    SDLK_DOLLAR:       Key.DOLLAR,
    SDLK_PERCENT:      Key.PERCENT,
    SDLK_CARET:        Key.CARET,
    SDLK_AMPERSAND:    Key.AMPERSAND,
    SDLK_ASTERISK:     Key.ASTERISK,
    SDLK_LEFTPAREN:    Key.LEFT_PAREN,
    SDLK_RIGHTPAREN:   Key.RIGHT_PAREN,
    SDLK_MINUS:        Key.DASH,
    SDLK_UNDERSCORE:   Key.UNDERSCORE,
    SDLK_PLUS:         Key.PLUS,
    SDLK_EQUALS:       Key.EQUAL,
    SDLK_LEFTBRACKET:  Key.LEFT_BRACKET,
    SDLK_RIGHTBRACKET: Key.RIGHT_BRACKET,
    # SDL has no { or }.
    SDLK_COLON:        Key.COLON,
    SDLK_SEMICOLON:    Key.SEMICOLON,
    SDLK_QUOTE:        Key.QUOTE,
    SDLK_QUOTEDBL:     Key.DOUBLE_QUOTE,
    SDLK_SLASH:        Key.SLASH,
    SDLK_BACKSLASH:    Key.BACKSLASH,
    # SDL has no |.
    SDLK_LESS:         Key.LESS,
    SDLK_GREATER:      Key.MORE,
    SDLK_PERIOD:       Key.PERIOD,
    SDLK_COMMA:        Key.COMMA,
    SDLK_QUESTION:     Key.QUESTION,
    SDLK_BACKQUOTE:    Key.GRAVE,
    # SDL has no ~, ± or §.

    SDLK_F1:  Key.F1,
    SDLK_F2:  Key.F2,
    SDLK_F3:  Key.F3,
    SDLK_F4:  Key.F4,
    SDLK_F5:  Key.F5,
    SDLK_F6:  Key.F6,
    SDLK_F7:  Key.F7,
    SDLK_F8:  Key.F8,
    SDLK_F9:  Key.F9,
    SDLK_F10: Key.F10,
    SDLK_F11: Key.F11,
    SDLK_F12: Key.F12,
    SDLK_F13: Key.F13,
    SDLK_F14: Key.F14,
    SDLK_F15: Key.F15,
    SDLK_F16: Key.F16,
    SDLK_F17: Key.F17,
    SDLK_F18: Key.F18,
    SDLK_F19: Key.F19,
    SDLK_F20: Key.F20,
    SDLK_F21: Key.F21,
    SDLK_F22: Key.F22,
    SDLK_F23: Key.F23,
    SDLK_F24: Key.F24,

    SDLK_ESCAPE:       Key.ESCAPE,
    SDLK_LSHIFT:       Key.LEFT_SHIFT,
    SDLK_RSHIFT:       Key.RIGHT_SHIFT,
    SDLK_TAB:          Key.TAB,
    SDLK_LCTRL:        Key.LEFT_CONTROL,
    SDLK_RCTRL:        Key.RIGHT_CONTROL,
    SDLK_LALT:         Key.LEFT_ALT,
    SDLK_RALT:         Key.RIGHT_ALT,
    SDLK_LGUI:         Key.LEFT_META,
    SDLK_RGUI:         Key.RIGHT_META,
    # SDL has no Fn.
    SDLK_APPLICATION:  Key.MENU,

    SDLK_CAPSLOCK:     Key.CAPS_LOCK,
    SDLK_NUMLOCKCLEAR: Key.NUM_LOCK,
    SDLK_SCROLLLOCK:   Key.SCROLL_LOCK,
    SDLK_PRINTSCREEN:  Key.PRINT_SCREEN,

    SDLK_HOME:         Key.HOME,
    SDLK_END:          Key.END,
    SDLK_INSERT:       Key.INSERT,
    SDLK_DELETE:       Key.DELETE,
    SDLK_PAGEUP:       Key.PAGE_UP,
    SDLK_PAGEDOWN:     Key.PAGE_DOWN,
    SDLK_PAUSE:        Key.PAUSE,

    SDLK_LEFT:         Key.LEFT_ARROW,
    SDLK_RIGHT:        Key.RIGHT_ARROW,
    SDLK_UP:           Key.UP_ARROW,
    SDLK_DOWN:         Key.DOWN_ARROW,

    SDLK_BACKSPACE:    Key.BACKSPACE,
    # ???
    SDLK_RETURN:       Key.ENTER,
    SDLK_RETURN2:      Key.ENTER,

    SDLK_BRIGHTNESSDOWN:    Key.BRIGHTNESS_DOWN,
    SDLK_BRIGHTNESSUP:      Key.BRIGHTNESS_UP,
    SDLK_VOLUMEDOWN:        Key.VOLUME_DOWN,
    SDLK_VOLUMEUP:          Key.VOLUME_UP,
    SDLK_AUDIOMUTE:         Key.VOLUME_MUTE,
    SDLK_AUDIOPLAY:         Key.MEDIA_PLAY,
    SDLK_AUDIOSTOP:         Key.MEDIA_STOP,
    SDLK_AUDIOPREV:         Key.MEDIA_PREVIOUS,
    SDLK_AUDIONEXT:         Key.MEDIA_NEXT,
    SDLK_EJECT:             Key.MEDIA_EJECT,

    SDLK_WWW:        Key.INTERNET,
    SDLK_CALCULATOR: Key.CALCULATOR,
    SDLK_COMPUTER:   Key.COMPUTER,
    SDLK_POWER:      Key.POWER,

    SDLK_KP_0:         Key.KEYPAD_0,
    SDLK_KP_1:         Key.KEYPAD_1,
    SDLK_KP_2:         Key.KEYPAD_2,
    SDLK_KP_3:         Key.KEYPAD_3,
    SDLK_KP_4:         Key.KEYPAD_4,
    SDLK_KP_5:         Key.KEYPAD_5,
    SDLK_KP_6:         Key.KEYPAD_6,
    SDLK_KP_7:         Key.KEYPAD_7,
    SDLK_KP_8:         Key.KEYPAD_8,
    SDLK_KP_9:         Key.KEYPAD_9,
    # SDL has no Keypad Insert and Keypad Delete.
    SDLK_KP_ENTER:     Key.KEYPAD_ENTER,
    # SDL has no Keypad Home and Keypad End.
    SDLK_KP_DIVIDE:    Key.KEYPAD_SLASH,
    SDLK_KP_MULTIPLY:  Key.KEYPAD_ASTERISK,
    SDLK_KP_MINUS:     Key.KEYPAD_DASH,
    SDLK_KP_PLUS:      Key.KEYPAD_PLUS,
    # SDL has no Keypad Page Up and Keypad Page Down.
}

MOD_MAPPING = {
    KMOD_LSHIFT:  [Key.SHIFT, Key.LEFT_SHIFT],
    KMOD_RSHIFT:  [Key.SHIFT, Key.RIGHT_SHIFT],
    KMOD_LCTRL:   [Key.CONTROL, Key.LEFT_CONTROL],
    KMOD_RCTRL:   [Key.CONTROL, Key.RIGHT_CONTROL],
    KMOD_LALT:    [Key.ALT, Key.LEFT_ALT],
    KMOD_RALT:    [Key.ALT, Key.RIGHT_ALT],
    KMOD_LGUI:    [Key.META, Key.LEFT_META],
    KMOD_RGUI:    [Key.META, Key.RIGHT_META],
    KMOD_CAPS:    [Key.CAPS_LOCK],
    KMOD_NUM:     [Key.NUM_LOCK],
    KMOD_MODE:    [Key.RIGHT_ALT]
}

ALSO_SEND = {
    SDLK_LSHIFT:  [Key.SHIFT],
    SDLK_RSHIFT:  [Key.SHIFT],
    SDLK_LCTRL:   [Key.CONTROL],
    SDLK_RCTRL:   [Key.CONTROL],
    SDLK_LALT:    [Key.ALT],
    SDLK_RALT:    [Key.ALT],
    SDLK_LGUI:    [Key.META],
    SDLK_RGUI:    [Key.META]
}



def handle_event(ev):
    if ev.type in (SDL_KEYDOWN, SDL_KEYUP):
        sym = ev.key.keysym.sym
        nativesym = ('SDL', sym)

        if sym in _map_cache:
            mapsyms = _map_cache[sym]
        else:
            mapsyms = [ KEY_MAPPING.get(sym, Key.OTHER) ] + ALSO_SEND.get(sym, [])
            _map_cache[sym] = mapsyms

        if ev.key.repeat:
            event = 'input.keyboard.repeat'
        elif ev.type == SDL_KEYDOWN:
            event = 'input.keyboard.press'
        else:
            event = 'input.keyboard.release'

        for mapsym in mapsyms:
            rave.events.emit(event, mapsym, nativesym)
    elif ev.type == SDL_TEXTEDITING:
        pass
    elif ev.type == SDL_TEXTINPUT:
        pass
    else:
        return False

    return True


## Internals.

_map_cache = {}

