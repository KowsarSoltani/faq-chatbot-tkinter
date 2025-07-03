import json
import tkinter as tk
from tkinter import messagebox, ttk
from fuzzywuzzy import process

def normalize_text(text):
    # Convert Arabic Yeh (U+064A) to Persian Yeh (U+06CC)
    text = text.replace('\u064A', '\u06CC')
    # Remove extra spaces
    text = ' '.join(text.strip().split())
    # Remove punctuation marks
    text = text.rstrip('؟!')
    return text

def load_faq_data():
    try:
        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            for item in data:
                item['keywords'] = [normalize_text(kw) for kw in item['keywords']]
                item['questions'] = [normalize_text(q) for q in item['questions']]
            return data
    except FileNotFoundError:
        messagebox.showerror("Error", "Data file not found.")
        return []
    except json.JSONDecodeError:
        messagebox.showerror("Error", "JSON file is invalid.")
        return []

# Keyword matching
def keyword_in_text(keyword, text):
    keyword = normalize_text(keyword)
    text = normalize_text(text)
    match = process.extractOne(keyword, [text], scorer=process.fuzz.partial_ratio)
    threshold = 70 if keyword in ["خوبی", "خوبی؟"] else (90 if len(keyword) <= 4 else 80)
    print(f"Match: keyword='{keyword}', text='{text}', score={match[1] if match else None}, threshold={threshold}")
    return match[1] >= threshold if match else False

# Find possible answers
def find_possible_answers(user_input, faq_data):
    matches = []
    for item in faq_data:
        for keyword in item['keywords']:
            if keyword_in_text(keyword, user_input):
                matches.append(item)
                break
        for question in item['questions']:
            match = process.extractOne(normalize_text(question), [normalize_text(user_input)], scorer=process.fuzz.partial_ratio)
            if match and match[1] >= 80:
                matches.append(item)
                break
    seen_answers = set()
    unique_matches = []
    for item in matches:
        if item['answer'] not in seen_answers:
            unique_matches.append(item)
            seen_answers.add(item['answer'])
    return unique_matches

# Display message in chat
def add_message(text, sender="user"):
    msg_frame = tk.Frame(chat_frame, bg="#f0f0f0")
    msg_frame.pack(fill="x", padx=10, pady=5)

    if sender == "user":
        bg_color = "#2196F3"
        fg_color = "#ffffff"
        justify = "right"
        anchor = "e"
    else:
        bg_color = "#E0E0E0"
        fg_color = "#333333"
        justify = "left"
        anchor = "w"

    msg_label = tk.Label(
        msg_frame,
        text=text,
        font=("Vazir", 12),
        bg=bg_color,
        fg=fg_color,
        wraplength=600,
        justify=justify,
        padx=10,
        pady=5
    )
    msg_label.pack(anchor=anchor, padx=5, pady=2)

    canvas.update()
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.yview_moveto(1.0)

# Show sub-questions
def show_subquestions(subquestions, parent_answer):
    add_message(parent_answer, sender="bot")
    if subquestions:
        add_message("Please choose one of the following options:", sender="bot")
        msg_frame = tk.Frame(chat_frame, bg="#f0f0f0")
        msg_frame.pack(fill="x", padx=10, pady=5)
        for key, value in subquestions.items():
            btn = ttk.Button(
                msg_frame,
                text=key,
                command=lambda val=value: show_answer(val),
                style="Chat.TButton"
            )
            btn.pack(pady=2, padx=5, fill="x")
        canvas.update()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(1.0)

# Show answer
def show_answer(subquestion_data):
    show_subquestions(subquestion_data.get('subquestions', {}), subquestion_data['answer'])

# Show possible answers
def show_answers(possible_answers):
    if not possible_answers:
        add_message(":( Unfortunately, I don't know the answer to this question.", sender="bot")
    elif len(possible_answers) == 1:
        main_answer = possible_answers[0]
        if 'subquestions' in main_answer and main_answer['subquestions']:
            show_subquestions(main_answer['subquestions'], main_answer['answer'])
        else:
            add_message(main_answer['answer'], sender="bot")
    else:
        add_message("Which of the following questions do you mean?", sender="bot")
        msg_frame = tk.Frame(chat_frame, bg="#f0f0f0")
        msg_frame.pack(fill="x", padx=10, pady=5)
        for answer in possible_answers:
            question = answer['questions'][0] if answer['questions'] else "No question"
            btn = ttk.Button(
                msg_frame,
                text=question,
                command=lambda ans=answer: show_subquestions(ans.get('subquestions', {}), ans['answer']),
                style="Chat.TButton"
            )
            btn.pack(pady=2, padx=5, fill="x")
        canvas.update()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(1.0)

# Handle asking question
def on_ask(event=None):
    user_input = normalize_text(entry_question.get().strip())
    if not user_input:
        add_message("Please enter your question.", sender="bot")
        return
    add_message(user_input, sender="user")
    possible_answers = find_possible_answers(user_input, faq_data)
    show_answers(possible_answers)
    entry_question.delete(0, tk.END)

# Main window
root = tk.Tk()
root.title("FAQ Chatbot")
root.geometry("800x600")
root.configure(bg="#f0f0f0")

# Configure ttk theme
style = ttk.Style()
style.theme_use("clam")
style.configure("Chat.TButton", font=("Vazir", 12), padding=10, background="#4CAF50", foreground="#ffffff")
style.configure("TEntry", font=("Vazir", 12), padding=5)
style.map("Chat.TButton", background=[("active", "#45a049")])

chat_container = tk.Frame(root, bg="#f0f0f0")
chat_container.pack(pady=10, padx=10, fill="both", expand=True)

canvas = tk.Canvas(chat_container, bg="#f0f0f0")
scrollbar = ttk.Scrollbar(chat_container, orient="vertical", command=canvas.yview)
chat_frame = tk.Frame(canvas, bg="#f0f0f0")

canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)
canvas.create_window((0, 0), window=chat_frame, anchor="nw")

def update_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

chat_frame.bind("<Configure>", update_scrollregion)

# Input frame
input_frame = tk.Frame(root, bg="#f0f0f0")
input_frame.pack(pady=10, padx=10, fill="x")

lbl_instruction = tk.Label(
    input_frame,
    text="😀What would you like to ask me?",
    font=("Vazir", 12, "bold"),
    bg="#f0f0f0",
    fg="#333333",
    justify="right"
)
lbl_instruction.pack(anchor="center")

entry_question = ttk.Entry(input_frame, width=50, font=("Vazir", 12), justify="right")
entry_question.pack(side="left", pady=5, padx=5)

btn_ask = ttk.Button(input_frame, text="Send", command=on_ask, style="Chat.TButton")
btn_ask.pack(side="left", pady=5)

entry_question.bind("<Return>", on_ask)

# Load data
faq_data = load_faq_data()

root.mainloop()
