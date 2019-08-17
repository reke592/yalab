from tkinter import *
app = Tk()
app.configure(bg='#eeeeee')

fmt = '%(hostname)20s %(ip)20s %(status)20s %(db)20s'
header = {}
header.setdefault('hostname', 'Computer Name')
header.setdefault('ip', 'IP Address')
header.setdefault('db', 'Default Blacklist')
header.setdefault('status', 'Status')

frm = Frame(app)
frm.pack()

listbox = Listbox(frm, width=50)
listbox.grid(column=0, row=1)

listbox.insert(0, fmt % header)
listbox.insert('end', fmt % { 'hostname': 'PC1', 'ip': '192.168.10.5', 'db': 'UPDATED', 'status': 'OFFLINE' })

app.mainloop()
