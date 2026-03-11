def main():
  from components.codenames import CodeNamesGame
  from components.cli import CLICodeNamesSpyMaster, CLICodeNamesGuesser
  from components.llm import LLMCodeNamesSpyMaster, LLMCodeNamesGuesser
  from components.ui import TKCodeNamesSpyMaster, TKCodeNamesGuesser
  # --------------------------------------- Defaults ---------------------------------------
  cfg = {
    'red_spymaster': 'llm',
    'red_guesser': 'ui',
    'blue_spymaster': 'llm',
    'blue_guesser': 'ui'
  }

  # --------------------------------------- Args ---------------------------------------
  import argparse
  parser = argparse.ArgumentParser(description="Play Codenames with different interfaces.")
  parser.add_argument("-rm", "--red_spymaster", choices=["cli", "llm", "ui"], default=cfg['red_spymaster'], help="Interface for Red SpyMaster")
  parser.add_argument("-rg", "--red_guesser", choices=["cli", "llm", "ui"], default=cfg['red_guesser'], help="Interface for Red Guesser")
  parser.add_argument("-bm", "--blue_spymaster", choices=["cli", "llm", "ui"], default=cfg['blue_spymaster'], help="Interface for Blue SpyMaster")
  parser.add_argument("-bg", "--blue_guesser", choices=["cli", "llm", "ui"], default=cfg['blue_guesser'], help="Interface for Blue Guesser")
  args = parser.parse_args()

  # --------------------------------------- Logging ---------------------------------------
  import logging
  _logger = logging.getLogger('codenames')
  _logger.setLevel(level=logging.DEBUG)
  _logger.addHandler(logging.StreamHandler())

  # --------------------------------------- Player setup ---------------------------------------
  class_map = {
    "cli": {
      "spymaster": CLICodeNamesSpyMaster,
      "guesser": CLICodeNamesGuesser
    },
    "llm": {
      "spymaster": LLMCodeNamesSpyMaster,
      "guesser": LLMCodeNamesGuesser
    },
    "ui": {
      "spymaster": TKCodeNamesSpyMaster,
      "guesser": TKCodeNamesGuesser
    }
  }
  red_spymaster = class_map[args.red_spymaster]["spymaster"]("Red")
  red_guesser = class_map[args.red_guesser]["guesser"]("Red")
  blue_spymaster = class_map[args.blue_spymaster]["spymaster"]("Blue")
  blue_guesser = class_map[args.blue_guesser]["guesser"]("Blue")
  
  # --------------------------------------- Game loop ---------------------------------------
  game = CodeNamesGame(red_spymaster, red_guesser, blue_spymaster, blue_guesser)

  done = False
  while not done:
    done = game.play_turn()
    game.game_state.pprint(show_colors=True)
  

if __name__ == "__main__":
  main()