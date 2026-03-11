from codenames import CodeNamesAction, CodeNamesActionType, CodeNamesGameState, CodeNamesGuesserInterface, CodeNamesPlayerInterface, CodeNamesSpyMasterInterface, CodeNamesWordType
from colorama import Fore, Style

class CLICodeNamesPlayer(CodeNamesPlayerInterface):
  def __init__(self, name: str, show_colors: bool):
    super().__init__()
    self.name = name
    self.show_colors = show_colors
    
  def print_gamestate(self):
    game_state = self.game_state
    print(f"\nYour turn ({self.name}):")
    game_state.pprint(show_colors=self.show_colors)

  def notify(self, game_state: CodeNamesGameState):
    self.game_state = game_state
    self.print_gamestate()


class CLICodeNamesSpyMaster(CLICodeNamesPlayer, CodeNamesSpyMasterInterface):
  def __init__(self, name: str):
    super().__init__(name=name + " (SpyMaster)", show_colors=True)

  def get_clue(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    self.game_state = game_state
    self.print_gamestate()
    while True:
      clue = input("Enter your clue (format: '<clue> <number>'):")
      try:
        clue_word, clue_number = clue.split()
        break
      except ValueError:
        print("Invalid input. Please try again.")
    return CodeNamesAction(action_type=CodeNamesActionType.CLUE, clue=clue_word, number=int(clue_number))

class CLICodeNamesGuesser(CLICodeNamesPlayer, CodeNamesGuesserInterface):
  def __init__(self, name: str):
    super().__init__(name=name + " (Guesser)", show_colors=False)

  def get_guess(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    self.game_state = game_state
    self.print_gamestate()
    while True:
      guess = input("Enter your guess (word position), or 'pass':")
      if 'pass'.startswith(guess.lower()) or guess.isnumeric():
        break
      else:
        print("Invalid input. Please try again.")

    if guess.isnumeric():
      return CodeNamesAction(action_type=CodeNamesActionType.GUESS, guess=int(guess))
    else:
      return CodeNamesAction(action_type=CodeNamesActionType.PASS)
