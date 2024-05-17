import itertools

data_folder = __file__[:-12] # change if file with user data is not in the same folder as this file
data_file = 'user_data.txt'
data_filename = data_folder + data_file
data = open(data_filename).readlines()

exec(f"filenames = {data[0]}")
exec(f"save_data = {data[1]}")

SOURCES = {}

for filename, data in zip(filenames, save_data):
    SOURCES[filename] = [data_folder + filename, data]

NONE_TYPABLES = ['Shift_L', 'Shift_R', 'Caps_Lock', 'Control_L','Control_R', 'Win_L', 'Alt_L', 'Alt_R', 'Control_R', 'Scroll_Lock', 'Pause', 'Insert', 'Home', 'Prior', 'Delete', 'End', 'Next', 'Escape', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'XF86Launch0', '??', 'XF86Mail', 'Num_Lock']

SAMPLE_SIZE = data['segment_size']

CURSOR = {'width': 8, 'height': 14}

WIN_CONFIG = {
    'x': 1000, 
    'y': 50, 
    'width': 500, 
    'height': 500, 
    'min_width': 300,
    'min_height': (SAMPLE_SIZE+6)*CURSOR['height'],
    'x_padding': 17, 
    'y_padding': 5,
    'b_padding': 35,
   }
