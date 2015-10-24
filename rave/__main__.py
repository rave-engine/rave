"""
rave entry point. Parse command line arguments and launch game.
"""
import argparse
import rave.bootstrap


def parse_arguments():
    parser = argparse.ArgumentParser(description='A modular and extensible visual novel engine.', prog='rave')
    parser.add_argument('-b', '--bootstrapper', help='Select bootstrapper to bootstrap the engine with. (default: autoselect)')
    parser.add_argument('-B', '--game-bootstrapper', metavar='BOOTSTRAPPER', help='Select bootstrapper to bootstrap the game with. (default: autoselect)')
    parser.add_argument('game', metavar='GAME', nargs='?', help='The game to run. Format dependent on used bootstrapper.')

    arguments = parser.parse_args()
    return arguments

def main():
    args = parse_arguments()
    engine = rave.bootstrap.bootstrap_engine(args.bootstrapper)
    engine.init()

    if args.game:
        game = rave.bootstrap.bootstrap_game(engine, args.game_bootstrapper, args.game)
        engine.run_game(game)

    engine.shutdown()

main()
