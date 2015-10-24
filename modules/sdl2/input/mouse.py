import rave.events
from rave.input import MouseButton
import sdl2

MOUSE_MAPPING = {
    sdl2.SDL_BUTTON_LEFT:   MouseButton.LEFT,
    sdl2.SDL_BUTTON_MIDDLE: MouseButton.MIDDLE,
    sdl2.SDL_BUTTON_RIGHT:  MouseButton.RIGHT
}


def handle_event(ev):
    if ev.type in (sdl2.SDL_MOUSEBUTTONDOWN, sdl2.SDL_MOUSEBUTTONUP):
        sym = ev.button.button
        mapsym = MOUSE_MAPPING.get(sym, MouseButton.OTHER)
        nativesym = ('SDL', sym)
        mouse = ev.button.which
        clicks = ev.button.clicks

        if mouse == sdl2.SDL_TOUCH_MOUSEID:
            return True

        if ev.type == sdl2.SDL_MOUSEBUTTONDOWN:
            event = 'input.mouse.press'
        else:
            event = 'input.mouse.release'

        rave.events.emit(event, mouse, mapsym, nativesym, clicks, (ev.motion.x, ev.motion.y))
    elif ev.type == sdl2.SDL_MOUSEMOTION:
        mouse = ev.motion.which
        if mouse == sdl2.SDL_TOUCH_MOUSEID:
            return True

        rave.events.emit('input.mouse.move', mouse, (ev.motion.x, ev.motion.y), (ev.motion.xrel, ev.motion.yrel))
    elif ev.type == sdl2.SDL_MOUSEWHEEL:
        mouse = ev.wheel.which
        if mouse == sdl2.SDL_TOUCH_MOUSEID:
            return True

        (x, y) = (ev.wheel.x, ev.wheel.y)
        if ev.wheel.direction == sdl2.SDL_MOUSEWHEEL_FLIPPED:
            x = -ev.wheel.x
            y = -ev.wheel.y

        rave.events.emit('input.mouse.scroll', mouse, (x, y))
    else:
        return False

    return True
