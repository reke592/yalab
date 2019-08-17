#
# ui.py
#
from tkinter import *
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import time

window = Tk()
window.title("Yalab")
window.geometry("350x200")
window.configure(bg="#d3d3d3")

style = ttk.Style()
style.theme_use('default')
style.configure('just_a_prefix.Horizontal.TProgressbar', background='light Green')


lbl = Label(window, text="test", bg="#d3d3d3", fg="Black")
lbl.grid(column=0, row=0)


btn = Button(window, text="Apply", bg="#eeeeee", fg="Black")
btn.grid(column=2, row=0)


txt = Entry(window, width=10, bg="White", fg="Black")
txt.grid(column=1, row=0)


combo = ttk.Combobox(window)
combo['values'] = (1,2,3,4,5,6, "TESTING")
combo.current(1)
combo.grid(column=0, row=1)


chk_tmp_state = BooleanVar()
chk_tmp_state.set(True)
chk_tmp = ttk.Checkbutton(window, text="Temporary Block", var=chk_tmp_state)
chk_tmp.grid(column=0, row=2)

chk_apply_all_state = BooleanVar()
chk_apply_all_state.set(False)
chk_apply_all = ttk.Checkbutton(window, text="Apply to all", var=chk_apply_all_state)
chk_apply_all.grid(column=1, row=2)


selected = IntVar()
rad1 = ttk.Radiobutton(window, text="First", value=1, var=selected)
rad1.grid(column=0, row=3)

rad2 = ttk.Radiobutton(window, text="Second", value=2, var=selected)
rad2.grid(column=1, row=3)

rad3 = ttk.Radiobutton(window, text="third", value=3, var=selected)
rad3.grid(column=2, row=3)


txtarea = scrolledtext.ScrolledText(window, width=40, height=10, bg="White", fg="Black")
txtarea.grid(column=0, row=4)


spin = Spinbox(window, from_=1, to=10, fg="Black", bg="White")
spin.grid(column=3, row=3)


bar = ttk.Progressbar(window, length=200, style='just_a_prefix.Horizontal.TProgressbar')
bar.grid(column=0, row=5)

def update_bar(v):
    bar['value'] = bar['value'] + v
    if bar['value'] == 100:
        messagebox.showinfo('system', 'finish')

btn.configure(command=lambda: update_bar(10))


files = filedialog.askopenfilenames()
print(files)

window.mainloop()

