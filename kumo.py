"""
* Author: "PepDebian(peppermintosteam@proton.me)
*
* License: SPDX-License-Identifier: GPL-3.0-or-later
*
* This is for the Kumo SSB Gui
"""

import os
import re
from urllib.parse import urljoin
from tkinter import filedialog
import sqlite3
import tkinter as tk
import requests
import ttkbootstrap as ttk
import bsconf


# setup the window
pwin = bsconf.bbstyle
pwin.resizable(False, False)
WINDOW_HEIGHT = 760
WINDOW_WIDTH = 1280
pwin.title('Peppermint Kumo (SSB Manager)')


# Set the user paths used
gusr = os.getlogin()
spath = "/home/" + gusr + "/.local/share/pmostools/peptools"
dpath = "/home/" + gusr + "/.local/share/applications/"
ipath = "/home/" + gusr + "/Pictures/"
# Set the window  icon
pwin.tk.call('wm', 'iconphoto', pwin,
             tk.PhotoImage(
                   file=spath + '/images/kumosm.png'))
# Set the database connection string
dcon = sqlite3.connect(spath + '/welval.db')
pcur = dcon.cursor()

# Create the table if not exists
pcur.execute(""" CREATE TABLE IF NOT EXISTS kumoapp (id integer PRIMARY
             KEY AUTOINCREMENT, ssbname text, lnk text);"""
             )

def download_favicon(url, output_folder=ipath, request_timeout=3):
    """ 
    This function will try a regex to find and locate the favicon 
    of a website.Depending on the website it may not find the favicon.
    the goals is to try and stay within the python stndard library
    """

    # Send a GET request to the website
    response = requests.get(url, timeout=request_timeout)
    response.raise_for_status()  # Raise an error for bad responses

    # Use a regular expression to find the favicon URL in the HTML
    match = re.search(
        r'<link[^>]*?rel=["\']?icon["\']?[^>]*?href=["\'](.*?)["\']', 
        response.text,
        re.IGNORECASE
        )
    if match:
        favicon_url = match.group(1)
        favicon_url = urljoin(url, favicon_url)
        # Download the favicon
        response = requests.get(favicon_url,timeout=request_timeout, stream=True)
        response.raise_for_status()
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        filename = os.path.join(output_folder,
                                os.path.basename(favicon_url)
                                )
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    return None


def delete_ssb():
    """ Delete the ssb that is selected """
    get_name = cmbo.get()
    link_address = """ DELETE FROM kumoapp WHERE ssbname = ? """
    pcur.execute(link_address, (get_name,))
    dcon.commit()
    runaddr_value.delete('1.0', tk.END)
    for dfile in os.listdir(dpath):
        if dfile.startswith(get_name) and dfile.endswith('.desktop'):
            del_path = os.path.join(dpath, dfile)
            os.remove(del_path)
    pwin.destroy()
    os.system('python3 refresh.py')


def center_screen():
    """ gets the coordinates of the center of the screen """
    screen_width = pwin.winfo_screenwidth()
    screen_height = pwin.winfo_screenheight()
    # Coordinates of the upper left corner of the window to make the window
    # appear in the center
    x_cordinate = int((screen_width / 2) - (WINDOW_WIDTH / 2))
    y_cordinate = int((screen_height / 2) - (WINDOW_HEIGHT / 2))
    pwin.geometry("{}x{}+{}+{}".format(WINDOW_WIDTH,
                                       WINDOW_HEIGHT, x_cordinate, y_cordinate
                                       )
                  )


def make_desktop_file():
    """ this will make the ssb and store in the Home folder"""
    get_name = ssb_value.get("1.0", 'end-1c')
    get_url = urladdr_value.get("1.0", 'end-1c')
    get_local = cmbomenu.get()
    get_icon = icon_value.get("1.0", 'end-1c')
    write_path = dpath + get_name + '.desktop'
    selected_category_key = categories_reverse[get_local]
    app_content = f"""
[Desktop Entry]
Name={get_name}
Exec= luakit -U  {get_url}
Icon={get_icon}
Categories={selected_category_key}
Type=Application
"""
    # Make sure path exists first
    folder = os.path.dirname(write_path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    # Then write the file
    with open(write_path, 'w') as app:
        app.write(app_content)


def add_new_ssb():
    """ Add new ssb """
    make_desktop_file()
    ssb_name = ssb_value.get("1.0", 'end-1c')
    ssb_address = urladdr_value.get("1.0", 'end-1c')
    sql_insert = """ INSERT INTO kumoapp(ssbname,lnk) VALUES(?,?);"""
    pcur.execute(sql_insert, (ssb_name, ssb_address,))
    dcon.commit()
    ssb_value.delete('1.0', tk.END)
    urladdr_value.delete('1.0', tk.END)
    pwin.destroy()
    os.system('python3 ' +  spath +  '/refresh.py')
    pwin.destroy()
    os.system('python3 refresh.py')


def fill_dropdown():
    """set the combobox value"""
    cursor = dcon.execute('SELECT ssbname FROM kumoapp')
    result = []
    for row in cursor.fetchall():
        result.append(row[0])
    return result


def fill_url_address():
    """ get the url of the ssb and run the it in lua"""
    get_name = cmbo.get()
    link_address = """ SELECT lnk FROM kumoapp WHERE ssbname = ? """
    pcur.execute(link_address, (get_name,))
    use_address = pcur.fetchone()
    runaddr_value.delete('1.0', tk.END)
    runaddr_value.insert("end-1c", use_address)


def run_url_address():
    """ Run the ssb with the run button"""
    run_addrs = runaddr_value.get("1.0", 'end-1c')
    os.system('luakit -U ' + run_addrs + ' &')

def select_icon():
    """ 
        Select the icon to be used for the SSB in the system
        The starting folder is the home pictures folder
    """
    ssb_address = urladdr_value.get("1.0", 'end-1c')
    output_filename = download_favicon(ssb_address)
    initial_dir = ipath
    file_path = filedialog.askopenfilename(
        title="Select Icon",
        initialdir=initial_dir,
        filetypes=[("Icon files", "*.ico"), ("Icon files", "*.png"),
                   ("Icon files", "*.gif"), ("Icon files", "*.ppm"),
                   ("Icon files", "*.pgm")]
    )
    if file_path:
        icon_value.delete(1.0, tk.END)
        icon_value.insert(tk.END, file_path)


### Create SSB side objects used
### Title
new_label = ttk.Label(pwin, text="Create new SSBs",
                      bootstyle="danger",
                      font=("Helvetica", 28)
                      )
new_label.place(x=20, y=40) #Change here x=10, y=20
ssb_label = ttk.Label(pwin, text="Give the ssb a name:", font=("", 18))
ssb_label.place(x=20, y=110) #Change x=10, y=55
ssb_value = tk.Text(pwin, height=1, width=25, font=("", 18)) #Change height=1, width=25, no font
ssb_value.place(x=20, y=160) #Change x=10, y=80
lblcmbomenu = ttk.Label(pwin, text="Menu Location:", font=("", 18))
lblcmbomenu.place(x=20, y=226) #Change x=10, y=113
categories = { 'AudioVideo' : 'AudioVideo',  'Audio':'Audio', 'Video':'Video',
               'Development':'Development', 'Education':'Education',
               'Game':'Game', 'Graphics':'Graphics', 'Network':'Internet',
               'Office':'Office', 'Settings':'Settings','System':'System',
               'Utility':'Utility'
                   }
categories_reverse = {value: key for key, value in categories.items()}
cmbomenu = ttk.Combobox(pwin)
cmbomenu.place(x=20, y=270) #Change x=10, y=135
cmbomenu['values'] = list(categories.values())
icon_default_text = 'Set the icon with the "Icon" button'
icon_value = tk.Text(pwin, height=2, width=32, font=("", 18)) #Change height=1, width=32
icon_value.insert(tk.END, icon_default_text)
icon_value.place(x=20, y=560)#Change x=10, y=280
icon_button = ttk.Button(pwin, text="Icon", width=14, cursor="hand2",
                        bootstyle="light-outline", command=select_icon
                        )
icon_button.place(x=180, y=648) #Change x=90, y=324
url_default_text = "example: https://www.example.com"
urladdr_label = ttk.Label(pwin, text="Enter the Url:", font=("", 18))
urladdr_label.place(x=20, y=344) #Change x=10, y=172
urladdr_value = tk.Text(pwin, height=3, width=32, font=("", 18)) #Change height=3, width=32
urladdr_value.insert(tk.END, url_default_text)
urladdr_value.place(x=20, y=400) #Change x=10, y=200

btnsv = ttk.Button(
    pwin,
    text="Save",
    cursor="hand2",
    bootstyle="light-outline",
    width=5,
    command=add_new_ssb
    )
btnsv.place(x=20, y=648) #Change x=10, y=324
### The Separator for the window
separator = ttk.Separator(pwin, orient='vertical')
separator.place(relx=.495, rely=0, relheight=1)
### Manage SSBs side)
manage_label = ttk.Label(pwin, text="Manage SSBs",
                         bootstyle="danger",
                         font=("Helvetica", 28) #Change font=("Helvetica", 14)
                         )
manage_label.place(x=660, y=40) #Change x=330 and y=20
lblcmbo = ttk.Label(pwin, text="Select SSB to Manage:",font=("", 18)) #Change no font
lblcmbo.place(x=660, y=110) #Change x=330, y=55
cmbo = ttk.Combobox(pwin, height=2, width=30, font=("", 18)) #Change no height, width, or font
cmbo.place(x=660, y=160) #Change x=330, y=80
cmbo['values'] = fill_dropdown()
runaddr_label = ttk.Label(pwin, text="Url Address:",font=("", 18)) #Change no font size
runaddr_label.place(x=660, y=250) #Change x=330, y=125
runaddr_value = tk.Text(pwin, height=4, width=38, font=("", 18)) #Change height=4, width=32, and no font
runaddr_value.place(x=660, y=300) #Change x=330, y=150
btnrun = ttk.Button(
    pwin,
    text="Run",
    cursor="hand2",
    bootstyle="light-outline",
    width=7,
    command=run_url_address
    )
btnrun.place(x=660, y=648)#Change x=330, y=324
btndelete = ttk.Button(
    pwin,
    text="Delete",
    cursor="hand2",
    bootstyle="light-outline",
    width=14, #Change width=7
    command=delete_ssb
    )
btndelete.place(x=860, y=648) #Change x=430, y=324


def set_state(event):
    """ 
    Function that managse the state of the buttons and the Url address
    for the Manage SSBs section, this is an event function
    """

    selected_value = cmbo.get()
    if selected_value == "":
        btndelete["state"] = "disabled"
        btnrun["state"] = "disabled"
    else:
        btndelete["state"] = "normal"
        btnrun["state"] = "normal"
        fill_url_address()

cmbo.bind("<<ComboboxSelected>>", set_state)
set_state(None)
center_screen()
pwin.mainloop()