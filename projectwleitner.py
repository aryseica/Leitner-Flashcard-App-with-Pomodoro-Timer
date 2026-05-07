"""Leitner Flashcard App with Pomodoro Timer.

This program implements a flashcard system based on the Leitner method, 
allowing users to add, review, and manage flashcards. It also includes a 
Pomodoro timer that rewards users with breaks based on their review 
performance. The app uses Tkinter for the GUI and JSON for data persistence.

Author: Mary Therese Unica Galvez
"""

import json
import os
import tkinter as tk
from tkinter import simpledialog, messagebox

FILENAME = "cards.json"

def load_cards():
    if os.path.exists(FILENAME):
        with open(FILENAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_cards(cards):
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)

class FlashcardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Leitner Flashcard App with Pomodoro Timer")
        
        # Initialize data
        self.cards = load_cards()
        self.timer_running = False
        self.time_left = 1500 # 25 minutes
        self.timer_mode = "STUDY"
        
        # Setup UI
        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(padx=45, pady=40)

        # Display Listbox for flashcards
        self.listbox = tk.Listbox(frame, width=45, height=16, font=("Courier", 10))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.update_listbox()

        btn_frame = tk.Frame(frame)
        btn_frame.pack(side=tk.LEFT, expand=True, padx=15)

        tk.Button(btn_frame, text="Add Card", command=self.add_card, width=18).pack(fill=tk.X)
        tk.Button(btn_frame, text="Delete Card", command=self.delete_card, width=18).pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Review Now", command=self.review_cards, width=18, bg="#d1d1d1").pack(fill=tk.X)

        # Timer UI
        self.mode_label = tk.Label(btn_frame, text="MODE: STUDY", fg="red", font=("Courier", 10, "bold"))
        self.mode_label.pack(pady=(20, 0))
        self.timer_label = tk.Label(btn_frame, text="25:00", font=("Helvetica", 20, "bold"), fg="red")
        self.timer_label.pack()
        self.timer_btn = tk.Button(btn_frame, text="Start Clock", command=self.toggle_timer)
        self.timer_btn.pack(fill=tk.X)
        tk.Button(btn_frame, text="Reset Clock", command=self.reset_timer).pack(fill=tk.X, pady=2)

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for card in self.cards:
            # Display level to show mastery progress
            lvl = card.get('Level', 1)
            self.listbox.insert(tk.END, f"Lvl {lvl} | {card['Definition']}")

    def add_card(self):
        word = simpledialog.askstring("New Card:", f"\n\n{' '*20}Word:{' '*20}\n\n")
        if not word: return
        definition = simpledialog.askstring("New Card:", f"\n\n{' '*20}Definition:{' '*20}\n\n")
        if definition is None: return
        # Cards start at Level 1 in the Leitner System
        self.cards.append({"Word": word, "Definition": definition, "Level": 1})
        self.update_listbox()
        save_cards(self.cards)

    def delete_card(self):
        sel = self.listbox.curselection()
        if not sel: return
        self.cards.pop(sel[0])
        self.update_listbox()
        save_cards(self.cards)

    def review_cards(self):
        if not self.cards:
            messagebox.showinfo("Info", "No cards to review.")
            return

        total_score = 0
        actual_reviewed = 0
        total_available = len(self.cards)

        # Sort cards so user reviews cards from the lowest (unfamiliar) to the highest level
        sorted_cards = sorted(self.cards, key=lambda x: x.get('Level', 1))

        for card in sorted_cards:
            if 'Level' not in card: card['Level'] = 1
            
            # Prompt asks for the terminology
            answer = simpledialog.askstring("Review", f"\n[Level {card['Level']}]\n\n{' '*20} {card['Definition']}{' '*20}\n\n")
            if answer is None: break
            
            actual_reviewed += 1
            if answer.strip().lower() == card["Word"].lower():
                # Success: Promote to next level (Max 5)
                card['Level'] = min(card['Level'] + 1, 5)
                total_score += 1
                messagebox.showinfo("Correct!", f"Promoted to Level {card['Level']}!")
            else:
                # Failure: Drop back to Level 1
                card['Level'] = 1
                messagebox.showinfo("Wrong", f"Dropped to Level 1!\nCorrect: {card['Word']}")
        
        # After review, update the main listbox to show new levels
        self.update_listbox()

        # Break Rewards
        if actual_reviewed == total_available:
            self.calculate_reward(total_score, total_available)
        elif actual_reviewed > 0:
            messagebox.showwarning("Incomplete", "Finish the whole deck to earn a break bonus!")
            # Auto-start the 25-minute study timer for incomplete reviews
            self.reset_timer()
            self.start_clock(1500)

        save_cards(self.cards)

    def calculate_reward(self, score, total):
        percentage = (score / total) * 100
        self.timer_mode = "BREAK"
        self.mode_label.config(text="MODE: BREAK", fg="green")
        self.timer_label.config(fg="green")
        self.lift() # Ensure popup is visible

        base = 300 # 5 mins
        if percentage == 100:
            choice = messagebox.askyesno("Perfect!", "100% Mastery! 10m break?\n(No = restart study)")
            if choice: self.start_clock(600)
            else: self.reset_timer(); self.start_clock(1500)
        elif 75 <= percentage < 100:
            choice = messagebox.askyesno("Great!", f"{percentage:.0f}% Mastery! Break: 8m 45s\n(No = restart study)")
            if choice: self.start_clock(base + 225)
            else: self.reset_timer(); self.start_clock(1500)
        elif 50 <= percentage < 75:
            choice = messagebox.askyesno("Good", f"Score: {percentage:.0f}% Mastery! Break: 7m 30s\n(No = restart study)")
            if choice: self.start_clock(base + 150)
            else: self.reset_timer(); self.start_clock(1500)
        else:
            choice = messagebox.askyesno("Results", "Standard 5m break.\n(No = restart study)")
            if choice: self.start_clock(base)
            else: self.reset_timer(); self.start_clock(1500)

    # Timer Engine 
    def toggle_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.timer_btn.config(text="Pause")
            self.update_timer()
        else:
            self.timer_running = False
            self.timer_btn.config(text="Resume")

    def reset_timer(self):
        self.timer_running = False
        self.timer_mode = "STUDY"
        self.time_left = 1500
        self.mode_label.config(text="MODE: STUDY", fg="red")
        self.timer_label.config(text="25:00", fg="red")
        self.timer_btn.config(text="Start Clock")

    def update_timer(self):
        if self.timer_running and self.time_left > 0:
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.time_left -= 1
            self.after(1000, self.update_timer)
        elif self.time_left <= 0:
            self.timer_running = False
            if self.timer_mode == "STUDY":
                messagebox.showinfo("Time Up", "Study over! Start review to earn your break.")
            else:
                self.reset_timer()
                self.start_clock(1500)

    def start_clock(self, seconds):
        self.time_left = seconds
        self.timer_running = True
        self.timer_btn.config(text="Pause")
        self.update_timer()

if __name__ == "__main__":
    app = FlashcardApp()
    app.mainloop()
