from .codenames import (
  CodeNamesAction, CodeNamesActionType, CodeNamesGameState,
  CodeNamesGuesserInterface, CodeNamesPlayerInterface, CodeNamesSpyMasterInterface, CodeNamesWordType
)
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langsmith import traceable

# --------------------------------------- Env Setup ---------------------------------------
from dotenv import load_dotenv
load_dotenv()
import os
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables.")
if not os.getenv("LANGSMITH_API_KEY"):
    raise ValueError("LANGSMITH_API_KEY not found in environment variables.")

# --------------------------------------- Logging ---------------------------------------
import logging
_logger = logging.getLogger('codenames.llm')

# --------------------------------------- Pydantic Models ---------------------------------------
class ClueModel(BaseModel):
    "Model for a clue action provided by the SpyMaster."
    clue: str = Field(..., description="The clue word provided by the SpyMaster")
    number: int = Field(..., description="The number of words related to the clue")

class GuessModel(BaseModel):
    "Model for a guess action, which can be either a word guess or a pass."
    guess: Optional[int] = Field(None, description="Position of the guessed word, or None if passing")
    pass_turn: bool = Field(False, description="Whether the guesser chooses to pass their turn")

# --------------------------------------- LLM PlayerInterface ---------------------------------------
class LLMCodeNamesPlayer(CodeNamesPlayerInterface):
  def __init__(self, name: str):
    super().__init__(name=name)

  def notify(self, game_state: CodeNamesGameState):
    self.game_state = game_state

# --------------------------------------- SpyMaster ---------------------------------------
class LLMCodeNamesSpyMaster(LLMCodeNamesPlayer, CodeNamesSpyMasterInterface):
  def __init__(self, name: str):
    super().__init__(name=name)
    self.llm = ChatOpenAI(model="gpt-5.2", temperature=0.7)

  def get_clue(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    clue_action = self.get_clue_traceable(game_state)
    return clue_action

  @traceable(name="SpyMaster Clue Generation")
  def get_clue_traceable(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    self.game_state = game_state

    clue_prompt_template = (
        "You are the SpyMaster in a game of Codenames. The grid has the following words:\n"
        "Your Words: {ours}\n Your Revealed Words: {revealed_ours}\n"
        "Opponent's Words: {theirs}\n Opponent's Revealed Words: {revealed_theirs}\n"
        "Assassin Word: {assassin}\n"
        "Provide a clue that relates {word_count} of your team's words without relating to the opponent's words or the assassin.\n"
        "Links can fall into one or more of the following categories\n"
        "1. Word continuations (e.g., to link 'bottle' and 'gun' you could use 'water-' with a hyphen indicating it)\n"
        "2. Categorical (e.g., to link 'apple' and 'banana' you could use 'fruit')\n"
        "3. Semantic associations (e.g., to link 'beach' and 'sun' you could use 'summer')\n"
        "4. Gaming/Pop culture references (e.g. to link 'Blizzard' and 'Winston' you could use 'Overwatch')\n"
        "DO NOT:\n"
        "1. Use verbatim words or word sections (e.g. 'fireman' as a clue for 'fire' and 'man')\n"
        "2. Use hints that depend on the word order, spelling, or pronunciation\n"
        "Start your response with the reasoning behind the selection and then the clue in the format: '<clue> <number>'.\n"
    )

    ours = [
      word.word for i, word in enumerate(game_state.words)
      if game_state.current_team.color_matches(word.color) and not game_state.is_revealed(i)
    ]
    revealed_ours = [
      word.word for i, word in enumerate(game_state.words)
      if game_state.current_team.color_matches(word.color) and game_state.is_revealed(i)
    ]
    theirs = [
      word.word for i, word in enumerate(game_state.words)
      if game_state.current_team.opposite().color_matches(word.color) and not game_state.is_revealed(i)
    ]
    revealed_theirs = [
      word.word for i, word in enumerate(game_state.words)
      if game_state.current_team.opposite().color_matches(word.color) and game_state.is_revealed(i)
    ]
    assassin = next((word.word for i, word in enumerate(game_state.words) if word.color == CodeNamesWordType.ASSASSIN), "No Assassin Word")
    word_count = game_state.ai_config['word_count'][game_state.current_team]

    clue_prompt = clue_prompt_template.format(
        ours=", ".join(ours) if ours else "None",
        theirs=", ".join(theirs) if theirs else "None",
        revealed_ours=", ".join(revealed_ours) if revealed_ours else "None",
        revealed_theirs=", ".join(revealed_theirs) if revealed_theirs else "None",
        assassin=assassin,
        word_count=word_count
    )
    clue_response = self.llm.invoke(clue_prompt)

    format_prompt_template = (
      "Extract the clue and number from this paragraph and provide them in the requested format:\n {clue}"
    )
    format_prompt = format_prompt_template.format(clue=clue_response)
    format_response: ClueModel = self.llm.with_structured_output(ClueModel).invoke(format_prompt) # type: ignore

    return CodeNamesAction(action_type=CodeNamesActionType.CLUE, clue=format_response.clue, number=format_response.number)

# --------------------------------------- Guesser ---------------------------------------
class LLMCodeNamesGuesser(LLMCodeNamesPlayer, CodeNamesGuesserInterface):
  def __init__(self, name: str):
    super().__init__(name=name)
    self.llm = ChatOpenAI(model="gpt-5.2", temperature=0.7)

  def get_guess(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    guess_action = self.get_guess_traceable(game_state)
    return guess_action

  @traceable(name="Guesser Guess Generation")
  def get_guess_traceable(self, game_state: CodeNamesGameState) -> CodeNamesAction:
    self.game_state = game_state
    
    guess_prompt_template = (
        "You are a Guesser in a game of Codenames. The grid has the following words currently unrevealed:\n"
        "Unrevealed Words: {grid}\n"
        "Your Revealed Words: {revealed_ours}\n"
        "Opponent's Revealed Words: {revealed_theirs}\n"
        "The SpyMaster has given the clue: '{clue}' for {number} words.\n"
        "Based on the clue, select one word from the grid that you think matches the clue. You can also choose to pass if you are unsure.\n"
        "Start your response with the reasoning behind the selection and then the guess in the format: 'guess <word-number>. <word>' or 'pass' if you choose to pass."
    )

    grid = [
      f'{i}. {word.word}' for i, word in enumerate(game_state.words)
      if not game_state.is_revealed(i)
    ]
    revealed_ours = [
      word.word for i, word in enumerate(game_state.words)
      if game_state.current_team.color_matches(word.color) and game_state.is_revealed(i)
    ]
    revealed_theirs = [
      word.word for i, word in enumerate(game_state.words)
      if game_state.current_team.opposite().color_matches(word.color) and game_state.is_revealed(i)
    ]

    clue_obj = game_state.last_clue()
    clue = clue_obj.clue if clue_obj else "No clue provided"
    number = clue_obj.number if clue_obj else 0

    guess_prompt = guess_prompt_template.format(
        grid=", ".join(grid) if grid else "None",
        revealed_ours=", ".join(revealed_ours) if revealed_ours else "None",
        revealed_theirs=", ".join(revealed_theirs) if revealed_theirs else "None",
        clue=clue,
        number=number
    )

    guess_response = self.llm.invoke(guess_prompt)

    format_prompt_template = (
      "Extract the guessed word's number from this response. If the response indicates a pass, set the guess to None and pass_turn to True. Otherwise, set pass_turn to False.\n"
      "Response: {guess}"
    )
    format_prompt = format_prompt_template.format(guess=guess_response)
    format_response: GuessModel = self.llm.with_structured_output(GuessModel).invoke(format_prompt) # type: ignore

    if format_response.pass_turn:
      return CodeNamesAction(action_type=CodeNamesActionType.PASS)
    else:
      return CodeNamesAction(action_type=CodeNamesActionType.GUESS, guess=format_response.guess)

