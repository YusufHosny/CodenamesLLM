import tkinter as tk
from tkinter import ttk, messagebox
from codenames import (
    CodeNamesAction, CodeNamesActionType, CodeNamesGameState, 
    CodeNamesGuesserInterface, CodeNamesSpyMasterInterface, CodeNamesWordType
)

class TKCodeNamesBase:
    """Base UI class to handle window setup and board rendering."""
    def __init__(self, title: str):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("800x700")
        
        self.colors = {
            CodeNamesWordType.RED: "#ff5252",
            CodeNamesWordType.BLUE: "#448aff",
            CodeNamesWordType.NEUTRAL: "#e0e0e0",
            CodeNamesWordType.ASSASSIN: "#212121",
            "HIDDEN": "#f5f5f5"
        }
        
        self.header = tk.Label(self.root, text=title, font=("Helvetica", 18, "bold"), pady=10)
        self.header.pack()
        
        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.controls_frame = tk.Frame(self.root, pady=20)
        self.controls_frame.pack(fill="x")
        
        self.return_val = None
        self.wait_var = tk.IntVar()

    def clear_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

class TKCodeNamesSpyMaster(TKCodeNamesBase, CodeNamesSpyMasterInterface):
    def __init__(self, name: str):
        super().__init__(f"SpyMaster: {name}")
        self.setup_controls()

    def setup_controls(self):
        tk.Label(self.controls_frame, text="Clue Word:").pack(side="left", padx=5)
        self.clue_entry = tk.Entry(self.controls_frame)
        self.clue_entry.pack(side="left", padx=5)
        
        tk.Label(self.controls_frame, text="Count:").pack(side="left", padx=5)
        self.count_entry = tk.Entry(self.controls_frame, width=5)
        self.count_entry.pack(side="left", padx=5)
        
        self.submit_btn = tk.Button(self.controls_frame, text="Submit Clue", command=self.submit_clue, bg="#4caf50", fg="white")
        self.submit_btn.pack(side="left", padx=10)

    def submit_clue(self):
        clue = self.clue_entry.get().strip()
        count = self.count_entry.get().strip()
        if clue and count.isdigit():
            self.return_val = CodeNamesAction(
                action_type=CodeNamesActionType.CLUE, 
                clue=clue, 
                number=int(count)
            )
            self.wait_var.set(1)
        else:
            messagebox.showwarning("Invalid Input", "Provide a word and a numeric count.")

    def get_clue(self, game_state: CodeNamesGameState) -> CodeNamesAction:
        self.clear_grid()
        rows, cols = game_state.dims
        for i, word_obj in enumerate(game_state.words):
            color = self.colors[word_obj.color]
            font_style = ("Helvetica", 10, "overstrike" if game_state.revealed[i] else "bold")
            lbl = tk.Label(self.grid_frame, text=word_obj.word.upper(), bg=color, 
                           fg="white" if word_obj.color != CodeNamesWordType.NEUTRAL else "black",
                           font=font_style, relief="ridge", width=15, height=4)
            lbl.grid(row=i // cols, column=i % cols, sticky="nsew", padx=2, pady=2)

        for i in range(rows): self.grid_frame.rowconfigure(i, weight=1)
        for i in range(cols): self.grid_frame.columnconfigure(i, weight=1)

        self.root.wait_variable(self.wait_var)
        return self.return_val

class TKCodeNamesGuesser(TKCodeNamesBase, CodeNamesGuesserInterface):
    def __init__(self, name: str):
        super().__init__(f"Guesser: {name}")
        self.pass_btn = tk.Button(self.controls_frame, text="Pass Turn", command=self.pass_turn, 
                                  bg="#f44336", fg="white", font=("Helvetica", 12))
        self.pass_btn.pack()
        self.clue_label = tk.Label(self.root, text="", font=("Helvetica", 12, "italic"))
        self.clue_label.pack()

    def pass_turn(self):
        self.return_val = CodeNamesAction(action_type=CodeNamesActionType.PASS)
        self.wait_var.set(1)

    def make_guess(self, index: int):
        self.return_val = CodeNamesAction(action_type=CodeNamesActionType.GUESS, guess=index)
        self.wait_var.set(1)

    def get_guess(self, game_state: CodeNamesGameState) -> CodeNamesAction:
        self.clear_grid()
        last_clue = game_state.last_clue()
        if last_clue:
            self.clue_label.config(text=f"Current Clue: {last_clue.clue} ({last_clue.number})")

        rows, cols = game_state.dims
        for i, word_obj in enumerate(game_state.words):
            revealed = game_state.revealed[i]
            bg_color = self.colors[word_obj.color] if revealed else self.colors["HIDDEN"]
            fg_color = "black" if not revealed or word_obj.color == CodeNamesWordType.NEUTRAL else "white"
            
            btn = tk.Button(self.grid_frame, text=word_obj.word.upper(), bg=bg_color, fg=fg_color,
                            font=("Helvetica", 10, "bold"), relief="raised",
                            command=lambda idx=i: self.make_guess(idx))
            
            if revealed:
                btn.config(state="disabled", relief="sunken")
            
            btn.grid(row=i // cols, column=i % cols, sticky="nsew", padx=2, pady=2)

        for i in range(rows): self.grid_frame.rowconfigure(i, weight=1)
        for i in range(cols): self.grid_frame.columnconfigure(i, weight=1)

        self.root.wait_variable(self.wait_var)
        return self.return_val