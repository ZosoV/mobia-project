import argparse
import os
import tkinter as tk
from PIL import Image, ImageTk
from tkinter.filedialog import asksaveasfilename

# Loading path through parser configuration
parser = argparse.ArgumentParser()
parser.add_argument(
    "path", help="Container directory of license plate images", type=str
)
args = parser.parse_args()

# UNIQUE_LICENSE_PLATES = set()

FILES = sorted(os.listdir(args.path))
COLLECTION = {}

# Command to write in txt
def save_file():
    for i in range(0, len(FILES), 2):
        plate_info = COLLECTION[i].plate_entry.get()

        # print(plate_info)

        with open(f"{args.path}/{COLLECTION[i].id}.txt", "w") as file:
            file.write(plate_info)


class Plate:
    def __init__(self, id, i, frame):
        self.id = id
        self.i = i
        self.frame = frame

    # Show the file name
    def text(self):
        plate_text = tk.Label(self.frame, text=self.id)
        plate_text.grid(column=1, row=self.i + 1, padx=5, pady=5)

    # Create license plate entry
    def entry(self):
        with open(f"{args.path}/{self.id}.txt") as f:
            content = f.read()
        var = tk.StringVar()
        self.plate_entry = tk.Entry(self.frame, textvariable=var, width="15")
        self.plate_entry.insert(0, content)
        self.plate_entry.grid(column=2, row=self.i + 1, padx=5, pady=5)

    # Create the image object
    def image(self):
        self.crop = ImageTk.PhotoImage(
            Image.open(f"{args.path}/{self.id}.jpg")
        )
        self.plate_crop = tk.Label(self.frame, image=self.crop)
        self.plate_crop.grid(column=3, row=self.i + 1, padx=5, pady=5)

# Widget to set all information and allow scrollbar
class Example(tk.Frame):
    def __init__(self, parent):

        tk.Frame.__init__(self, parent)
        self.canvas = tk.Canvas(self, borderwidth=0)
        self.frame = tk.Frame(self.canvas)
        self.vsb = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window(
            (4, 4), window=self.frame, anchor="nw", tags="self.frame"
        )

        self.frame.bind("<Configure>", self.onFrameConfigure)

        # Headers
        header_file = tk.Label(self.frame, text="File Name")
        header_file.grid(column=1, row=0, padx=5, pady=5)
        header_plate = tk.Label(self.frame, text="License Plate")
        header_plate.grid(column=2, row=0, padx=5, pady=5)
        header_img = tk.Label(self.frame, text="Image")
        header_img.grid(column=3, row=0, padx=5, pady=5)

        self.populate()

    def populate(self):

        # Load each license plate in folder
        for i in range(0, len(FILES), 2):
            id = FILES[i].split(".")[0]

            COLLECTION[i] = Plate(id, i, self.frame)

            COLLECTION[i].text()
            COLLECTION[i].entry()
            COLLECTION[i].image()

    # Reset the scroll region to encompass the inner frame
    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


if __name__ == "__main__":
    # Setting master
    app = tk.Tk()
    app.geometry("500x500")
    app.title("License Plate Labeler")
    app.resizable(False, False)

    app.rowconfigure(0, weight=1)
    app.columnconfigure(1, weight=1)
    
    # Loading information
    example = Example(app)
    example.grid(row=0, column=1, sticky="nsew")

    # Creating Save button
    frm_buttons = tk.Frame(app, relief=tk.RAISED, bd=2)
    btn_save = tk.Button(frm_buttons, text="Save", command=save_file)
    btn_save.grid(row=1, column=0, sticky="ew", padx=5)
    frm_buttons.grid(row=0, column=0, sticky="ns")

    app.mainloop()
