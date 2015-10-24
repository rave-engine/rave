import sdl2
import rave.input


def handle_event(ev):
    """ XXX: Broken right now with regard to coordinate handling. Need to investigate. """
    if ev.type in (sdl2.SDL_FINGERDOWN, sdl2.SDL_FINGERUP):
        device = ev.tfinger.touchId
        finger = ev.tfinger.fingerId
        if ev.type == sdl2.SDL_FINGERDOWN:
            event = 'input.touch.press'
        else:
            event = 'input.touch.release'

        rave.events.emit(event, device, finger, (ev.tfinger.x, ev.tfinger.y), (ev.tfinger.dx, ev.tfinger.dy), ev.tfinger.pressure)
    elif ev.type == sdl2.SDL_FINGERMOTION:
        device = ev.tfinger.touchId
        finger = ev.tfinger.fingerId

        rave.events.emit('input.touch.move', device, finger, (ev.tfinger.x, ev.tfinger.y), (ev.tfinger.dx, ev.tfinger.dy), ev.tfinger.pressure)
    elif ev.type == sdl2.SDL_MULTIGESTURE:
        pass
    elif ev.type == sdl2.SDL_DOLLARGESTURE:
        pass
    else:
        return False

    return True
