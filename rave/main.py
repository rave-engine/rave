import rave.events
import rave.modularity
import rave.backends
import rave.resources
import rave.rendering


def init_game(game):
    rave.modularity.load_all()
    rave.events.emit('game.init', game)

    with game.env:
        rave.backends.select_all()


def run_game(game):
    running = True

    # Stop the event loop when a stop event was caught.
    def stop(event):
        nonlocal running
        running = False
    game.events.hook('game.stop', stop)


    rave.events.emit('game.start', game)
    with game.env:
        # Typical handle events -> update game state -> render loop.
        while running:
            with game.active_lock:
                # Suspend main loop while lock is active: useful for when the OS requests an application suspend.
                pass

            rave.backends.handle_events(game)
            if game.mixer:
                game.mixer.render(None)
            if game.window:
                game.window.render(None)
