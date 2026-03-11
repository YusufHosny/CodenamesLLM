from .codenames import (
  CodeNamesAction, CodeNamesActionType, CodeNamesGameState,
  CodeNamesGuesserInterface, CodeNamesPlayerInterface,
  CodeNamesSpyMasterInterface, CodeNamesWordType, CodeNamesTeam
)
import tkinter as tk

# --------------------------------------- Shared Root ---------------------------------------
_root = None

def _ensure_root():
  global _root
  if _root is None:
    _root = tk.Tk()
    _root.withdraw()
  return _root

# --------------------------------------- Color Constants ---------------------------------------
_BG_COLOR = {
  CodeNamesWordType.RED: '#dc3545',
  CodeNamesWordType.BLUE: '#0d6efd',
  CodeNamesWordType.NEUTRAL: '#f8d775',
  CodeNamesWordType.ASSASSIN: '#212529',
}
_FG_COLOR = {
  CodeNamesWordType.RED: 'white',
  CodeNamesWordType.BLUE: 'white',
  CodeNamesWordType.NEUTRAL: 'black',
  CodeNamesWordType.ASSASSIN: 'white',
}
_TEAM_BG = {
  CodeNamesTeam.RED: '#dc3545',
  CodeNamesTeam.BLUE: '#0d6efd',
}
_HIDDEN_BG = '#d6d8db'
_HIDDEN_FG = '#212529'

# --------------------------------------- TK PlayerInterface ---------------------------------------
class TKCodeNamesPlayer(CodeNamesPlayerInterface):
  def __init__(self, name: str, show_colors: bool):
    super().__init__(name=name)
    self.show_colors = show_colors
    self.game_state = None

    _ensure_root()
    self.window = tk.Toplevel(_root)
    self.window.title(f"Codenames - {self.name}")
    self.window.geometry("960x720")
    self.window.protocol("WM_DELETE_WINDOW", lambda: None)

    self._build_ui()

  def _build_ui(self):
    # Header
    self.header_frame = tk.Frame(self.window, bg='#343a40')
    self.header_frame.pack(fill=tk.X)
    self.header_label = tk.Label(
      self.header_frame, text=self.name,
      font=('Helvetica', 14, 'bold'), fg='white', bg='#343a40', pady=8
    )
    self.header_label.pack()

    # Main content: grid (left) + history (right)
    self.content_frame = tk.Frame(self.window)
    self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Grid
    self.grid_frame = tk.Frame(self.content_frame)
    self.grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # History
    history_outer = tk.LabelFrame(self.content_frame, text="History", font=('Helvetica', 10, 'bold'))
    history_outer.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
    self.history_text = tk.Text(
      history_outer, width=30, height=20,
      state=tk.DISABLED, wrap=tk.WORD, font=('Consolas', 9)
    )
    scrollbar = tk.Scrollbar(history_outer, command=self.history_text.yview)
    self.history_text.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.history_text.pack(fill=tk.BOTH, expand=True)

    self.history_text.tag_configure('red', foreground='#dc3545', font=('Consolas', 9, 'bold'))
    self.history_text.tag_configure('blue', foreground='#0d6efd', font=('Consolas', 9, 'bold'))
    self.history_text.tag_configure('detail', foreground='#495057')
    self.history_text.tag_configure('sep', foreground='#adb5bd')

    # Current clue display
    self.clue_frame = tk.Frame(self.window, bg='#f8f9fa')
    self.clue_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
    self.clue_label = tk.Label(
      self.clue_frame, text="Waiting for clue...",
      font=('Helvetica', 12, 'bold'), bg='#f8f9fa', fg='#495057', pady=4
    )
    self.clue_label.pack()

    # Input area (populated by subclasses)
    self.input_frame = tk.Frame(self.window)
    self.input_frame.pack(fill=tk.X, padx=10, pady=10)

    self.word_labels = []

  # --------------------------------------- Grid Rendering ---------------------------------------
  def _render_grid(self, game_state):
    for w in self.grid_frame.winfo_children():
      w.destroy()
    self.word_labels = []

    dims = game_state.dims
    for i, word_obj in enumerate(game_state.words):
      row, col = divmod(i, dims[1])
      revealed = game_state.is_revealed(index=i)

      if revealed:
        bg = _BG_COLOR[word_obj.color]
        fg = _FG_COLOR[word_obj.color]
        text = f"{i}. {word_obj.word.upper()}"
        relief = tk.SUNKEN
        font = ('Helvetica', 10, 'bold')
      elif self.show_colors:
        bg = _BG_COLOR[word_obj.color]
        fg = _FG_COLOR[word_obj.color]
        text = f"{i}. {word_obj.word.lower()}"
        relief = tk.RAISED
        font = ('Helvetica', 10)
      else:
        bg = _HIDDEN_BG
        fg = _HIDDEN_FG
        text = f"{i}. {word_obj.word.lower()}"
        relief = tk.RAISED
        font = ('Helvetica', 10)

      lbl = tk.Label(
        self.grid_frame, text=text, font=font,
        bg=bg, fg=fg, relief=relief,
        width=14, height=2, anchor='center'
      )
      lbl.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
      self.word_labels.append(lbl)

    for c in range(dims[1]):
      self.grid_frame.columnconfigure(c, weight=1)
    for r in range(dims[0]):
      self.grid_frame.rowconfigure(r, weight=1)

  # --------------------------------------- History Rendering ---------------------------------------
  def _get_history_with_teams(self, game_state):
    entries = []
    team = CodeNamesTeam.RED
    for action in game_state.history:
      entries.append((team, action))
      if action.action_type == CodeNamesActionType.GUESS and action.guess is not None:
        color = game_state.words[action.guess].color
        if color == CodeNamesWordType.ASSASSIN or not team.color_matches(color):
          team = team.opposite()
      elif action.action_type == CodeNamesActionType.PASS:
        team = team.opposite()
    return entries

  def _render_history(self, game_state):
    self.history_text.configure(state=tk.NORMAL)
    self.history_text.delete('1.0', tk.END)

    entries = self._get_history_with_teams(game_state)
    for team, action in entries:
      tag = team.value  # 'red' or 'blue'
      if action.action_type == CodeNamesActionType.CLUE:
        self.history_text.insert(tk.END, f"{'─' * 28}\n", 'sep')
        self.history_text.insert(tk.END, f"[{team.value.upper()}] ", tag)
        self.history_text.insert(tk.END, f"Clue: {action.clue} ({action.number})\n", 'detail')
      elif action.action_type == CodeNamesActionType.GUESS:
        word = game_state.words[action.guess].word if action.guess is not None else '?'
        color = game_state.words[action.guess].color if action.guess is not None else None
        result = ''
        if color is not None:
          if team.color_matches(color):
            result = ' ✓'
          elif color == CodeNamesWordType.ASSASSIN:
            result = ' ✗ ASSASSIN'
          else:
            result = ' ✗'
        self.history_text.insert(tk.END, f"  [{team.value.upper()}] ", tag)
        self.history_text.insert(tk.END, f"Guess: {word}{result}\n", 'detail')
      elif action.action_type == CodeNamesActionType.PASS:
        self.history_text.insert(tk.END, f"  [{team.value.upper()}] ", tag)
        self.history_text.insert(tk.END, "Pass\n", 'detail')

    self.history_text.configure(state=tk.DISABLED)
    self.history_text.see(tk.END)

  # --------------------------------------- Clue Display ---------------------------------------
  def _render_clue(self, game_state):
    clue = game_state.last_clue()
    if clue:
      fg = _TEAM_BG.get(game_state.current_team, '#495057')
      self.clue_label.configure(text=f"Clue: {clue.clue} ({clue.number})", fg=fg)
    else:
      self.clue_label.configure(text="Waiting for clue...", fg='#495057')

  # --------------------------------------- Update Display ---------------------------------------
  def _update_display(self, game_state):
    team_name = game_state.current_team.value.upper()
    team_bg = _TEAM_BG.get(game_state.current_team, '#343a40')
    self.header_label.configure(text=f"{self.name} \u2014 {team_name}'s Turn")
    self.header_frame.configure(bg=team_bg)
    self.header_label.configure(bg=team_bg)
    self._render_grid(game_state)
    self._render_history(game_state)
    self._render_clue(game_state)
    self.window.update()

  def notify(self, game_state):
    self.game_state = game_state
    self._update_display(game_state)

# --------------------------------------- SpyMaster ---------------------------------------
class TKCodeNamesSpyMaster(TKCodeNamesPlayer, CodeNamesSpyMasterInterface):
  def __init__(self, name: str):
    super().__init__(name=name + " (SpyMaster)", show_colors=True)
    self._build_spymaster_input()

  def _build_spymaster_input(self):
    tk.Label(self.input_frame, text="Clue:", font=('Helvetica', 11)).pack(side=tk.LEFT, padx=(0, 5))
    self.clue_entry = tk.Entry(self.input_frame, font=('Helvetica', 11), width=20)
    self.clue_entry.pack(side=tk.LEFT, padx=(0, 10))

    tk.Label(self.input_frame, text="Number:", font=('Helvetica', 11)).pack(side=tk.LEFT, padx=(0, 5))
    self.number_entry = tk.Entry(self.input_frame, font=('Helvetica', 11), width=5)
    self.number_entry.pack(side=tk.LEFT, padx=(0, 10))

    self.submit_btn = tk.Button(
      self.input_frame, text="Give Clue", font=('Helvetica', 11, 'bold'),
      bg='#28a745', fg='white', padx=15, pady=3,
      command=self._on_submit, state=tk.DISABLED
    )
    self.submit_btn.pack(side=tk.LEFT)

    self.error_label = tk.Label(self.input_frame, text="", fg='red', font=('Helvetica', 9))
    self.error_label.pack(side=tk.LEFT, padx=10)

    self._result_var = tk.StringVar(self.window)

  def _on_submit(self):
    clue = self.clue_entry.get().strip()
    number = self.number_entry.get().strip()

    if not clue or not number:
      self.error_label.configure(text="Enter both clue and number.")
      return
    if ' ' in clue:
      self.error_label.configure(text="Clue must be a single word.")
      return
    try:
      int(number)
    except ValueError:
      self.error_label.configure(text="Number must be an integer.")
      return

    self.error_label.configure(text="")
    self._result_var.set(f"{clue}|{number}")

  def get_clue(self, game_state):
    self.game_state = game_state
    self._update_display(game_state)

    # Clear and enable inputs
    self.clue_entry.delete(0, tk.END)
    self.number_entry.delete(0, tk.END)
    self.error_label.configure(text="")
    self.clue_entry.configure(state=tk.NORMAL)
    self.number_entry.configure(state=tk.NORMAL)
    self.submit_btn.configure(state=tk.NORMAL)
    self.clue_entry.focus_set()
    self.window.lift()

    # Bind Enter key
    self.clue_entry.bind('<Return>', lambda e: self._on_submit())
    self.number_entry.bind('<Return>', lambda e: self._on_submit())

    # Wait for submission
    self._result_var.set("")
    self.window.wait_variable(self._result_var)

    # Disable inputs
    self.submit_btn.configure(state=tk.DISABLED)
    self.clue_entry.configure(state=tk.DISABLED)
    self.number_entry.configure(state=tk.DISABLED)

    parts = self._result_var.get().split('|')
    return CodeNamesAction(
      action_type=CodeNamesActionType.CLUE,
      clue=parts[0], number=int(parts[1])
    )

# --------------------------------------- Guesser ---------------------------------------
class TKCodeNamesGuesser(TKCodeNamesPlayer, CodeNamesGuesserInterface):
  def __init__(self, name: str):
    super().__init__(name=name + " (Guesser)", show_colors=False)
    self._build_guesser_input()
    self._waiting = False

  def _build_guesser_input(self):
    self.pass_btn = tk.Button(
      self.input_frame, text="Pass Turn", font=('Helvetica', 11, 'bold'),
      bg='#6c757d', fg='white', padx=15, pady=3,
      command=self._on_pass, state=tk.DISABLED
    )
    self.pass_btn.pack(side=tk.LEFT)

    self.status_label = tk.Label(
      self.input_frame, text="Waiting for your turn...",
      font=('Helvetica', 10), fg='#495057'
    )
    self.status_label.pack(side=tk.LEFT, padx=15)

    separator = tk.Frame(self.input_frame, width=2, bg='#adb5bd')
    separator.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)

    tk.Label(self.input_frame, text="AI Word Count:", font=('Helvetica', 10)).pack(side=tk.LEFT, padx=(0, 5))
    self._word_count_var = tk.IntVar(self.window, value=2)
    self.word_count_slider = tk.Scale(
      self.input_frame, from_=1, to=5, orient=tk.HORIZONTAL,
      variable=self._word_count_var, font=('Helvetica', 10),
      length=120, showvalue=True
    )
    self.word_count_slider.pack(side=tk.LEFT)

    self._result_var = tk.IntVar(self.window, value=-1)

  def _on_word_click(self, index):
    if not self._waiting:
      return
    if self.game_state and self.game_state.is_revealed(index=index):
      return
    self._result_var.set(index)

  def _on_pass(self):
    if not self._waiting:
      return
    self._result_var.set(-2)

  def _render_grid(self, game_state):
    """Override to use clickable buttons for unrevealed words."""
    for w in self.grid_frame.winfo_children():
      w.destroy()
    self.word_labels = []

    dims = game_state.dims
    for i, word_obj in enumerate(game_state.words):
      row, col = divmod(i, dims[1])
      revealed = game_state.is_revealed(index=i)

      if revealed:
        bg = _BG_COLOR[word_obj.color]
        fg = _FG_COLOR[word_obj.color]
        text = f"{i}. {word_obj.word.upper()}"
        widget = tk.Label(
          self.grid_frame, text=text,
          font=('Helvetica', 10, 'bold'),
          bg=bg, fg=fg, relief=tk.SUNKEN,
          width=14, height=2, anchor='center'
        )
      else:
        bg = _HIDDEN_BG
        fg = _HIDDEN_FG
        text = f"{i}. {word_obj.word.lower()}"
        widget = tk.Button(
          self.grid_frame, text=text,
          font=('Helvetica', 10),
          bg=bg, fg=fg, relief=tk.RAISED,
          width=14, height=2, cursor='hand2',
          activebackground='#b0c4de',
          command=lambda idx=i: self._on_word_click(idx)
        )

      widget.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
      self.word_labels.append(widget)

    for c in range(dims[1]):
      self.grid_frame.columnconfigure(c, weight=1)
    for r in range(dims[0]):
      self.grid_frame.rowconfigure(r, weight=1)

  def get_guess(self, game_state):
    self.game_state = game_state
    game_state.ai_config['word_count'] = str(self._word_count_var.get())
    self._update_display(game_state)

    self._waiting = True
    self.pass_btn.configure(state=tk.NORMAL)
    self.status_label.configure(text="Click a word to guess, or pass")
    self.window.lift()

    self._result_var.set(-1)
    self.window.wait_variable(self._result_var)

    self._waiting = False
    self.pass_btn.configure(state=tk.DISABLED)

    result = self._result_var.get()
    if result == -2:
      self.status_label.configure(text="Passed.")
      return CodeNamesAction(action_type=CodeNamesActionType.PASS)
    else:
      word = game_state.words[result].word
      self.status_label.configure(text=f"Guessed: {word}")
      return CodeNamesAction(action_type=CodeNamesActionType.GUESS, guess=result)
