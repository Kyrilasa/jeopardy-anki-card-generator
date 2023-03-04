import datetime
import random
import threading
import tkinter as tk
import genanki
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import Calendar
from tkinter import filedialog
from scrape_lib import get_game_urls_before_date, scrape
import babel.numbers
# Create a tkinter window
window = tk.Tk()

# Set the window title
window.title("Jeopardy! Scraper")

# Set the window size
window.geometry("400x400")

# Create a frame for the date field
date_frame = ttk.Frame(window)
date_frame.pack(side="top", pady=10)

# Create a label for the date field
label = ttk.Label(date_frame, text="Select a date:")
label.pack(side="left")

# Create a date field using the tkcalendar module
cal = Calendar(date_frame, selectmode="day", year=2023, month=3, day=3)
cal.pack(side="left")

# Create a label for the save file field
save_label = ttk.Label(window, text="Save file:")
save_label.pack(pady=10)

# Create a text field for displaying the selected file path
save_text = ttk.Entry(window, state="readonly")
save_text.pack(pady=10)

# Create a button for selecting the save file


def select_file():
    # Show a file dialog for selecting a file path
    file_path = filedialog.asksaveasfilename(defaultextension=".apkg")

    # Set the text field value to the selected file path
    save_text.configure(state="normal")
    save_text.delete(0, tk.END)
    save_text.insert(0, file_path)
    save_text.configure(state="readonly")


file_button = ttk.Button(window, text="Select File", command=select_file)
file_button.pack(pady=10)

# Create a submit button
submit_button = ttk.Button(window, text="Start")
submit_button.pack(pady=10)


def generate_anki_deck(game_urls, file_path, selected_date_formatted, current_date_formatted, progress_bar_callback):
    new_deck = genanki.Deck(
        random.randrange(1 << 30, 1 << 31),
        f'Jeopardy deck [{selected_date_formatted}<->{current_date_formatted}]')

    jeopardy_model = genanki.Model(
        random.randrange(1 << 30, 1 << 31),
        'Jeopardy [updated]',
        fields=[
            {'name': 'Answer'},
            {'name': 'Question'},
            {'name': 'Value'},
            {'name': 'Category'},
            {'name': 'Value'},
            {'name': 'Air Date'},
            {'name': 'Round'},
        ],
        templates=[
            {'id': 1,
                'name': 'Jeopardy',
                'qfmt': '\n{{Round}}<br>\n{{Category}}<br>\n{{Value}}<br>\n{{Question}}\n',
                'afmt': '\n    {{FrontSide}}\n            <hr id=answer>\n                   {{Answer}}<br>\n                   {{Air Date}}\n',
             },
        ],
        css='.card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n',
    )
    total_num_of_urls = len(game_urls)
    for idx, show_object in enumerate(scrape(game_urls)):
        air_date = show_object['air_date']
        for round in show_object['rounds']:
            for question in round['questions']:
                jeopardy_note = genanki.Note(
                    model=jeopardy_model,
                    fields=[question['answer'], question['prompt'], question['value'], question['category'], question['value'], air_date, round['round_id']], sort_field=question['prompt'])
                new_deck.add_note(jeopardy_note)
        progress_bar_callback(idx+1, total_num_of_urls)
    genanki.Package(new_deck).write_to_file(file_path)


def submit():

    # Get the selected file path from the text field
    file_path = save_text.get()

    if file_path == "":
        # Display an alert message
        messagebox.showerror(
            "Error", "Please select and name an output file")
        return
    # Get the selected date from the calendar widget
    date = cal.get_date()
    current_date_obj = datetime.datetime.now()
    selected_date_obj = datetime.datetime.strptime(
        date, '%m/%d/%y')
    if selected_date_obj > current_date_obj:
        # Display an alert message
        messagebox.showerror(
            "Error", "Please select a date in the past or present.")
        return
    formatted_date = selected_date_obj.strftime("%Y-%m-%d")
    # Disable the date field, the file dialog button, and the save file text field
    cal.configure(state="disabled")
    file_button.configure(state="disabled")
    save_text.configure(state="disabled")

    # Create a new window for the loading screen
    loading_window = tk.Toplevel(window)
    loading_window.geometry("400x150+500+200")
    loading_window.title("Loading...")
    loading_window.resizable(False, False)
    loading_window.overrideredirect(True)
    loading_window.grab_set()

    # Create a label with the loading message
    message_label = ttk.Label(
        loading_window, text="Generating Anki deck, please wait...")
    message_label.pack(pady=10)

    # Create a progress bar
    progress_bar = ttk.Progressbar(
        loading_window, mode="determinate", length=200)
    progress_bar.pack(pady=10)

    def update_progress(current_value, total_value):
        progress_percent = int((current_value / total_value) * 100)
        progress_bar['value'] = progress_percent
        message_label['text'] = f"Generating Anki deck, please wait...{current_value} / {total_value} shows scraped"
        # calculate the ETA
        loading_window.update_idletasks()

    # Call the generate_anki_deck function in a separate thread

    def generate_deck():
        game_urls = get_game_urls_before_date(formatted_date)
        generate_anki_deck(game_urls, file_path, formatted_date,
                           current_date_obj.strftime("%Y-%m-%d"), update_progress)

        # Stop the progress bar
        progress_bar.stop()

        # Destroy the loading window
        loading_window.destroy()

        # Show the submit button, the date field, the file dialog button, the save file label, and the save file text field again
        date_frame.pack(side="top", pady=10)
        save_label.pack(pady=10)
        save_text.pack(pady=10)
        file_button.pack(pady=10)
        submit_button.pack(pady=10)

        # Enable the date field, the file dialog button, and the save file text field
        cal.configure(state="normal")
        file_button.configure(state="normal")
        save_text.configure(state="normal")

    # Start the generate_deck function in a separate thread
    loading_window.after(100, lambda: threading.Thread(
        target=generate_deck).start())


# Assign the submit function to the button
submit_button.configure(command=submit)

# Run the tkinter event loop
if __name__ == "__main__":
    window.mainloop()
