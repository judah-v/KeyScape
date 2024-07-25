import os


data_folder = os.path.dirname(__file__) + '\\' # change if file with user data is not in the same folder as this file
data_file = 'user_data.txt'
data_filename = data_folder + data_file
raw_data = open(data_filename).readlines()

exec(f"SOURCES = {raw_data[0]}")
exec(f"USER_DATA = {raw_data[1]}")

NONE_TYPABLES = ['Shift_L', 'Shift_R', 'Caps_Lock', 'Control_L','Control_R', 'Win_L', 'Alt_L', 'Alt_R', 'Control_R', 'Scroll_Lock', 'Pause', 'Insert', 'Home', 'Prior', 'Delete', 'End', 'Next', 'Escape', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'XF86Launch0', '??', 'XF86Mail', 'Num_Lock', 'Up', 'Down', 'Left', 'Right']

SAMPLE_SIZE = USER_DATA['settings']['sample_size']

CURSOR = {'width': 8, 'height': 14}

WIN_CONFIG = {
    'x': 1000, 
    'y': 50, 
    'width': 500, 
    'height': 400, 
    'min_width': 300,
    'min_height': 300,
    'x_padding': 17, 
    'y_padding': 5,
    'bottom_padding': 50,
   }
# ^ change this to a class and use relative minimums so you only have to change 
# the defaults and not both (unless you want to)
