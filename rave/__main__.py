import argparse
import sys
from os import path


def parse_arguments():
    parser = argparse.ArgumentParser(description='A modular and extensible visual novel engine.', prog='rave')
    parser.add_argument('-b', '--bootstrapper', help='Select bootstrapper to bootstrap the engine with. (default: autoselect)')
    parser.add_argument('-B', '--game-bootstrapper', metavar='BOOTSTRAPPER', help='Select bootstrapper to bootstrap the game with. (default: autoselect)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging.')
    parser.add_argument('game', metavar='GAME', nargs='?', help='The game to run. Format dependent on used bootstrapper.')

    arguments = parser.parse_args()
    return arguments

def main():
    args = parse_arguments()

    if args.debug:
        from . import log
        log.Logger.LEVEL |= log.DEBUG

    from . import bootstrap
    bootstrap.bootstrap_engine(args.bootstrapper)
    bootstrap.bootstrap_game(args.game_bootstrapper, args.game)

main()
