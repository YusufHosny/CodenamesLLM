import os
import random
import enum
from typing import List, Optional, Tuple
from abc import ABC
    
import logging

from colorama import Fore, Style
_logger = logging.getLogger('codenames.game')

# ---------------------------------------- Config ---------------------------------------
class CONFIG:
  WORDS_FILE = os.path.join(os.path.dirname(__file__), '..', 'words.txt')
  NUM_WORDS = 25
  DIM_X = 5
  DIM_Y = 5
  NUM_RED = 9
  NUM_BLUE = 8
  NUM_NEUTRAL = 7
  NUM_ASSASSIN = 1

# --------------------------------------- Enums ---------------------------------------
class CodeNamesWordType(enum.Enum):
  RED = 'red'
  BLUE = 'blue'
  NEUTRAL = 'neutral'
  ASSASSIN = 'assassin'

  def get_text_modifier(self) -> str:
    color_map = {
      CodeNamesWordType.RED: Fore.RED,
      CodeNamesWordType.BLUE: Fore.BLUE,
      CodeNamesWordType.NEUTRAL: Fore.WHITE,
      CodeNamesWordType.ASSASSIN: Fore.BLACK,
    }
    return color_map[self]

class CodeNamesTeam(enum.Enum):
  RED = 'red'
  BLUE = 'blue'

  def opposite(self):
    return CodeNamesTeam.BLUE if self == CodeNamesTeam.RED else CodeNamesTeam.RED
  
  def color_matches(self, word_type: CodeNamesWordType) -> bool:
    if self == CodeNamesTeam.RED:
      return word_type == CodeNamesWordType.RED
    else:
      return word_type == CodeNamesWordType.BLUE

class CodeNamesActionType(enum.Enum):
  CLUE = 'clue'
  GUESS = 'guess'
  PASS = 'pass'

# --------------------------------------- Data Classes ---------------------------------------
class CodeNamesWord:
  def __init__(self, word: str, color: CodeNamesWordType):
    self.word = word
    self.color = color

class CodeNamesAction:
  def __init__(self,
               action_type: CodeNamesActionType,
               clue: Optional[str] = None,
               number: Optional[int] = None,
               guess: Optional[int] = None
               ):
    self.action_type = action_type
    self.clue = clue
    self.number = number
    self.guess = guess
    self.validate()

  def validate(self):
    if self.action_type == CodeNamesActionType.CLUE:
      if self.clue is None or self.number is None:
        raise ValueError("Clue action must have clue and number")
    elif self.action_type == CodeNamesActionType.GUESS:
      if self.guess is None:
        raise ValueError("Guess action must have guess index")
    elif self.action_type == CodeNamesActionType.PASS:
      pass
    else:
      raise ValueError(f"Invalid action type: {self.action_type}")

class CodeNamesGameState:
  def __init__(self, words: List[CodeNamesWord]):
    self.words = words
    self.revealed = [False] * len(words)
    self.current_team = CodeNamesTeam.RED
    self.game_over = False
    self.dims = (CONFIG.DIM_X, CONFIG.DIM_Y)
    self.ai_config = {
      'word_count': {
        CodeNamesTeam.RED: '2 or more',
        CodeNamesTeam.BLUE: '2 or more'
      }
    }
    self.history = []

  def reveal_word(self, index: int):
    self.revealed[index] = True
    return self.words[index].color
  
  def is_game_over(self) -> Tuple[bool, Optional[CodeNamesTeam]]:
    red_remaining = sum(
      1 for i, word in enumerate(self.words)
      if word.color == CodeNamesWordType.RED and not self.revealed[i]
      )
    blue_remaining = sum(
      1 for i, word in enumerate(self.words)
      if word.color == CodeNamesWordType.BLUE and not self.revealed[i]
      )
    assassin_revealed = any(
      self.revealed[i] and word.color == CodeNamesWordType.ASSASSIN
      for i, word in enumerate(self.words)
      )
    
    self.game_over = assassin_revealed or red_remaining == 0 or blue_remaining == 0
    if assassin_revealed:
      return True, self.current_team.opposite()
    elif red_remaining == 0:
      return True, CodeNamesTeam.RED
    elif blue_remaining == 0:
      return True, CodeNamesTeam.BLUE
    else:
      return False, None

  def append_history(self, action: CodeNamesAction):
    self.history.append(action)

  def is_revealed(self, index: Optional[int] = None, word: Optional[str] = None) -> bool:
    if index is not None:
      return self.revealed[index]
    if word is not None:
      try:
        index = next(i for i, w in enumerate(self.words) if w.word == word)
        return self.revealed[index]
      except StopIteration:
        return False
    return False

  def last_clue(self) -> Optional[CodeNamesAction]:
    for action in reversed(self.history):
      if action.action_type == CodeNamesActionType.CLUE:
        return action
    return None
  
  def last_guess(self) -> Optional[CodeNamesAction]:
    for action in reversed(self.history):
      if action.action_type == CodeNamesActionType.GUESS:
        return action
    return None
  
  def change_team(self):
    self.current_team = self.current_team.opposite()

  def pprint(self, show_colors: bool = False):
    word_grid = [self.words[i:i+self.dims[1]] for i in range(0, len(self.words), self.dims[1])]
    word_position = 0
    for row in word_grid:
      for word_obj in row:
        display_word = word_obj.word.upper() if self.is_revealed(word=word_obj.word) else word_obj.word.lower()
        if len(display_word) < 15:
          display_word = display_word.ljust(15)
        modifier = Fore.YELLOW
        if show_colors or self.is_revealed(word=word_obj.word):
          modifier = word_obj.color.get_text_modifier()
        if self.is_revealed(word=word_obj.word):
          print(f"{modifier}{word_position}. {display_word}{Style.RESET_ALL}", end="\t")
        else:
          print(f"{modifier}{word_position}. {display_word}{Style.RESET_ALL}", end="\t")
        word_position += 1
      print("\n")

# --------------------------------------- Player Interfaces ---------------------------------------
class CodeNamesPlayerInterface(ABC):
  def __init__(self, name: str):
    self.name = name

  def notify(self, game_state: CodeNamesGameState):
    raise NotImplementedError("This method should be implemented by subclasses")

class CodeNamesGuesserInterface(CodeNamesPlayerInterface):
  def get_guess(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    raise NotImplementedError("This method should be implemented by subclasses")
  
class CodeNamesSpyMasterInterface(CodeNamesPlayerInterface):
  def get_clue(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    raise NotImplementedError("This method should be implemented by subclasses")
  
# --------------------------------------- Game Logic ---------------------------------------
class CodeNamesGame:
  def __init__(self,
               red_spymaster: CodeNamesSpyMasterInterface,
               red_guesser: CodeNamesGuesserInterface,
               blue_spymaster: CodeNamesSpyMasterInterface,
               blue_guesser: CodeNamesGuesserInterface
               ):
    self.red_spymaster = red_spymaster
    self.red_guesser = red_guesser
    self.blue_spymaster = blue_spymaster
    self.blue_guesser = blue_guesser
    self.players = [red_spymaster, red_guesser, blue_spymaster, blue_guesser]
    self.initialize()

  def initialize(self):
    self.initialize_words()
    self.initialize_game_state()
    
  def initialize_words(self):
    words = self.load_words()
    sampled = random.sample(words, CONFIG.NUM_WORDS)
    words_with_colors = self.assign_roles(sampled)
    random.shuffle(words_with_colors)
    self.words = words_with_colors

  def initialize_game_state(self):
    self.game_state = CodeNamesGameState(self.words)

  def load_words(self):
      with open(CONFIG.WORDS_FILE) as f:
        words = [line.strip() for line in f]
        return words
      
  def assign_roles(self, words: List[str]) -> List[CodeNamesWord]:
      reds = [
        CodeNamesWord(word, CodeNamesWordType.RED) for word in words[:CONFIG.NUM_RED]
        ]
      blues = [
        CodeNamesWord(word, CodeNamesWordType.BLUE)
        for word in words[CONFIG.NUM_RED:CONFIG.NUM_RED+CONFIG.NUM_BLUE]
        ]
      neutrals = [
        CodeNamesWord(word, CodeNamesWordType.NEUTRAL)
        for word in words[CONFIG.NUM_RED+CONFIG.NUM_BLUE:CONFIG.NUM_RED+CONFIG.NUM_BLUE+CONFIG.NUM_NEUTRAL]
        ]
      assassins = [
        CodeNamesWord(word, CodeNamesWordType.ASSASSIN)
        for word in words[CONFIG.NUM_RED+CONFIG.NUM_BLUE+CONFIG.NUM_NEUTRAL:CONFIG.NUM_RED+CONFIG.NUM_BLUE+CONFIG.NUM_NEUTRAL+CONFIG.NUM_ASSASSIN]
        ]
      return reds + blues + neutrals + assassins

  def play_turn(self):
    spymaster = self.red_spymaster if self.game_state.current_team == CodeNamesTeam.RED else self.blue_spymaster
    spymaster_action = spymaster.get_clue(self.game_state)
    self.handle_clue(spymaster_action)

    guesser = self.red_guesser if self.game_state.current_team == CodeNamesTeam.RED else self.blue_guesser
    can_keep_guessing = True
    while can_keep_guessing:
      guesser_action = guesser.get_guess(self.game_state)
      can_keep_guessing = self.handle_guesser_action(guesser_action)

    game_over, winner = self.game_state.is_game_over()
    if game_over and winner is not None:
      self.handle_game_over(winner)
      return True
    else:
      return False

  def handle_spymaster_action(self, action: CodeNamesAction):
    if action.action_type == CodeNamesActionType.CLUE:
      self.handle_clue(action)
    else:
      _logger.warning(f"Unexpected action type from spymaster: {action.action_type}")

  def handle_guesser_action(self, action: CodeNamesAction):
    if action.action_type == CodeNamesActionType.GUESS:
      return self.handle_guess(action)
    elif action.action_type == CodeNamesActionType.PASS:
      return self.handle_pass(action)
    else:
      _logger.warning(f"Unexpected action type from guesser: {action.action_type}")
      return False

  def handle_clue(self, action: CodeNamesAction):
    _logger.info(f"{self.game_state.current_team.value} gives clue: {action.clue} ({action.number})")
    self.game_state.append_history(action)
    for player in self.players:
      player.notify(self.game_state)
 
  def handle_guess(self, action: CodeNamesAction):
    _logger.info(f"{self.game_state.current_team.value} guesses: {action.guess}")
    self.game_state.append_history(action)

    if action.guess is None:
      _logger.warning("Guess action missing guess index")
      return
    
    color = self.game_state.reveal_word(action.guess)
    _logger.info(f"Revealed word: {self.game_state.words[action.guess].word} ({color.value})")

    if color == CodeNamesWordType.ASSASSIN:
      _logger.info(f"{self.game_state.current_team.value} revealed the assassin! {self.game_state.current_team.opposite().value} team wins!")
      return False
    elif color == CodeNamesWordType.RED and self.game_state.current_team == CodeNamesTeam.RED:
      _logger.info(f"{self.game_state.current_team.value} guessed correctly!")
      return True
    elif color == CodeNamesWordType.BLUE and self.game_state.current_team == CodeNamesTeam.BLUE:
      _logger.info(f"{self.game_state.current_team.value} guessed correctly!")
      return True
    else:
      _logger.info(f"{self.game_state.current_team.value} guessed incorrectly.")
      self.game_state.change_team()
      return False

  def handle_pass(self, action: CodeNamesAction):
    _logger.info(f"{self.game_state.current_team.value} passes.")
    self.game_state.append_history(action)
    self.game_state.change_team()
    return False

  def handle_game_over(self, winner: CodeNamesTeam):
    _logger.info(f"Game over! {winner.value} team wins!")