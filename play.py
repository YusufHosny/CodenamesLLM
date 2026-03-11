def main():
  from components.codenames import CodeNamesGame
  from components.cli import CLICodeNamesSpyMaster, CLICodeNamesGuesser
  from components.llm import LLMCodeNamesSpyMaster, LLMCodeNamesGuesser

  import logging
  _logger = logging.getLogger('codenames')
  _logger.setLevel(level=logging.DEBUG)
  _logger.addHandler(logging.StreamHandler())

  red_spymaster = LLMCodeNamesSpyMaster()
  red_guesser = LLMCodeNamesGuesser()
  blue_spymaster = LLMCodeNamesSpyMaster()
  blue_guesser = LLMCodeNamesGuesser()

  game = CodeNamesGame(red_spymaster, red_guesser, blue_spymaster, blue_guesser)

  done = False
  while not done:
    done = game.play_turn()
    game.game_state.pprint(show_colors=True)
  

if __name__ == "__main__":
  main()