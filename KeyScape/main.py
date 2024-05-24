from importlib import reload
import tkinter as tk
import tkinter.messagebox as mb
import os
import resources 
import time
import string

#---------------------------------NOTEPAD---------------------------------------
# practice idea: use network ports and another client application to view typing
#                practice sessions in real time
# 
# prevent more than one practice page being opened simultaneously
# 
# add buttons to practice pages to navigate between text segments already 
# completed
# 
# create graph on home page to compare key accuracy
# 
# settings page to adjust line sampling size and other settings
#-------------------------------------------------------------------------------

def setup_user_profile():
    with open(resources.data_filename, 'r+', encoding='utf-8') as file:
        fnames, l_data, profile = [eval(line) for line in file.readlines()]
        for char in string.printable.replace('\r\x0b\x0c', ''):
            profile[char] = {'correct': 0, 'incorrect': 0}
        content = f'{repr(fnames)}\n{repr(l_data)}\n{repr(profile)}'
        file.seek(0)
        file.write(content)
        file.truncate()


def track_time(func):
    def wrapper(self, *args, **kwargs):
        char = args[0].keysym
        if char not in resources.NONE_TYPABLES+['BackSpace'] and not self.cursor.in_tab:
            stop = time.monotonic()
            start = self.last_keypress if self.last_keypress else stop
            self.time_taken += (stop-start)
            self.last_keypress = stop
        func(self, *args, **kwargs)
        return 
    return wrapper


def save_data(new_data, line):
    '''
    data -> [index, new_value]
    index = index of data in tuple in format (line number, number of lines per segment)
    '''

    with open(resources.data_filename, 'r+',encoding="UTF-8") as file:
        filenames, line_data, user_profile = [eval(l) for l in file.readlines()]
        cont = [filenames, line_data, user_profile]

        if line == 2:
            filename, new_data = new_data
            index = filenames.index(filename)
            line_data[index][new_data['key']] = new_data['value']
            cont = [filenames, line_data, user_profile]
        else:
            cont[line-1] = new_data

        content = '{0}\n{1}\n{2}'.format(*cont)
        file.seek(0)
        file.write(content)
        file.truncate()
    reload(resources)


def get_data(filename = '', line = 2):
    with open(resources.data_filename, encoding='utf-8') as file:
        filenames, s_data, err_profile = [eval(line) for line in file.readlines()]
        if filename:
            index = filenames.index(filename)
            s_data = s_data[index]
    
    return [filenames, s_data, err_profile][line-1]


class App:
    def __init__(self):
        self.Home = Page('KeyScape', app=self, kind='home')
        return
     
    def create_page(self, filename: str):
        name = filename
        sources = resources.SOURCES
        self.curr_line = sources[name][1]['line_no']
        curr_line = self.curr_line
        lines = open(sources[name][0], encoding="UTF-8").readlines()

        try:
            while lines[curr_line].lstrip(' ') == '\n':
                curr_line += 1
            line_data = [name, {'key': 'line_no', 'value': curr_line}]
            save_data(line_data, line=2)
            selection = lines[curr_line:curr_line + resources.SAMPLE_SIZE]
            txt = ''.join(selection)
            self.CurrentPage = Page(name, txt) # fix this. too ambiguous           
        except IndexError:
            print('You have hit the end of the file.')
            restart = mb.askokcancel('lesson completed', "You have completed the lesson. Would you like restart?")
            if restart:
                line_data = [name, {'key': 'line_no', 'value': 0}]
                save_data(line_data, line=2)
                self.create_page(filename)
                return
            
        return 
    
    def run(self):
        return self.Home.main.mainloop()


class Page:
    def __init__(self, title: str, 
                 text: str ='', 
                 app: App =None,
                 kind: str ='text', 
                 geometry=f"{resources.WIN_CONFIG['width']}x{resources.WIN_CONFIG['height']}+{resources.WIN_CONFIG['x']}+{resources.WIN_CONFIG['y']}", 
                 name='typing_page', dimensions=(resources.WIN_CONFIG['min_width'],
                 resources.WIN_CONFIG['min_height'])):
        main = tk.Tk(name)
        main.title(title)
        main.minsize(*dimensions)
        main.geometry(geometry)
        self.main = main
        if kind == 'home':
            self.App = app
            self.start_homepage()
        elif kind == 'text':
            self.start_practicepage(text)
        return
    

    def start_homepage(self):
        sources = resources.SOURCES
        for source in sources:
            btn = tk.Button(self.main, text=source, command=lambda: self.App.create_page(source))
            btn.place(x=50, y=50)
        return
    

    def start_practicepage(self, text: str):
        self.time_taken = 0
        self.displayed_text = ''
        self.collat_cursor = None
        self.displayed_text = self.display_text(text)
        first_char = self.displayed_text.lstrip()[0]
        self.cursor = Cursor(self.main, page=self, char=first_char, text=self.displayed_text)
        self.last_keypress = None
        self.curr_line = 0
        self.error_count = 0
        self.backspace_count = 0
        self.collateral_error_count = 0
        self.key_profiles = get_data(line=3)
        self.main.bind('<Key>', self.update)
        self.main.bind('<Motion>', self.pause)


    def display_text(self, txt: str, bg: str ='', fg: str ='black') -> str:
        WIN_CONFIG = resources.WIN_CONFIG
        CURSOR = resources.CURSOR
        max_length = max([len(l) for l in txt.splitlines()]) #get length of longest line in text
        x_pad = WIN_CONFIG['x_padding']
        y_pad = WIN_CONFIG['y_padding']
        bottom_pad = WIN_CONFIG['b_padding']
        c_width = CURSOR['width']
        c_height = CURSOR['height']
        new_wn_height = y_pad + (c_height + 2)*len(txt.splitlines()) + bottom_pad
        new_wn_width = x_pad*2 + c_width * max_length

        if new_wn_width < WIN_CONFIG['width']:
            wn_width = WIN_CONFIG['width']
        else:
            wn_width = new_wn_width
        if new_wn_height < WIN_CONFIG['height']:
            wn_height = WIN_CONFIG['height']
        else:
            wn_height = new_wn_height

        self.main.geometry(f'{wn_width}x{wn_height}')
        self.main.minsize(new_wn_width,new_wn_height)
        bg = self.main['bg'] if bg == '' else bg
        text = tk.Label(self.main, text=txt, font='courier 10', justify='left', bg=bg, fg=fg)
        text.place(x=x_pad,y=y_pad)
        return txt

    @track_time
    def update(self, event):
        page = self
        key_profiles = self.key_profiles
        cursor = self.cursor
        collat_cursor = self.collat_cursor
        disp_txt_lines = cursor.displayed_text.splitlines()

        for curs in [cursor, collat_cursor]:
            if curs and curs.text_pos == len(cursor.typable_text) -1:
                curs.at_end = True
                
        cursor.update_context()
        if collat_cursor:
            collat_cursor.update_context()
        
        if event.keysym in resources.NONE_TYPABLES:
            pass

        elif event.keysym == 'Tab':
            cursor.in_tab = True
            for i in range(cursor.tab_size):
                _event = tk.EventType.KeyPress
                _event.keysym = 'space'
                _event.char = ' '
                self.update(_event)
            cursor.in_tab = False

        elif event.char == cursor.char and cursor.current_errors == 0:
            key_profiles[cursor.char]['correct'] += 1
            cursor.color = 'green'
            cursor.from_backspace = False
            cursor.text_pos += 1
            cursor.line_pos += 1
            cursor.draw(cursor.next_char)

        elif event.char == '\r' and cursor.char == '\n' and cursor.current_errors == 0:
            cursor.color = 'green'
            cursor.line += 1
            cursor.line_pos = 0
            cursor.text_pos += 1
            cursor.draw(cursor.next_char)

        elif event.keysym == 'BackSpace':
            self.backspace_count += 1
            cursor.at_end = False

            if collat_cursor:
                collat_cursor.at_end = False
                
            if cursor.current_errors == 0 and cursor.text_pos > 0:
                cursor.line_pos -= 1
                cursor.text_pos -= 1
            elif cursor.current_errors > 0:
                cursor.color = 'red'
                cursor.draw(cursor.char)
                print('\n\n\n', cursor.current_errors,'\n\n\n')
                cursor.current_errors -= 1
                cursor.from_backspace = True
                if collat_cursor: 
                    collat_cursor.current_errors -= 1

            if cursor.prev_char == '\n' and not self.collat_cursor and cursor.text_pos > 0 and not cursor.from_backspace:
                cursor.line -= 1
                cursor.line_pos = len(disp_txt_lines[cursor.line])

            if cursor.current_errors == 0:
                cursor.color = 'green'
                if cursor.text_pos == 0:
                    cursor.draw(cursor.typable_text[0])

                else:
                    cursor.draw(cursor.char if cursor.from_backspace and cursor.text_pos > 0 else cursor.prev_char)
                    cursor.from_backspace = False

            if cursor.current_errors > 0 and collat_cursor:
                if cursor.current_errors == 1:
                    collat_cursor.Frame.destroy()
                    self.collat_cursor = None
                elif collat_cursor.prev_char == '\n':
                    collat_cursor.line -= 1
                    collat_cursor.line_pos = len(disp_txt_lines[collat_cursor.line]) 
                    collat_cursor.text_pos -= 1
                    collat_cursor.draw(collat_cursor.prev_char)
                else:
                    collat_cursor.line_pos -= 1
                    collat_cursor.text_pos -= 1
                    collat_cursor.draw(collat_cursor.prev_char)
        
        else:
            if cursor.color != 'red':
                key_profiles[cursor.char]['incorrect'] += 1
                self.error_count += 1
                cursor.color = 'red'
                cursor.draw(cursor.char)
                
            
            if cursor.current_errors == 1 and not cursor.at_end:
                self.collateral_error_count += 1
                x = cursor.startpos[0]
                y = cursor.startpos[1]
                self.collat_cursor = Cursor(self.main, x=x, y=y, page=page, color='gray', text=self.displayed_text)
                collat_cursor = self.collat_cursor
                collat_cursor.text_pos = cursor.text_pos + 1
                collat_cursor.line = cursor.line
                collat_cursor.line_pos = cursor.line_pos + 1
                collat_cursor.current_errors = cursor.current_errors
                if collat_cursor.text_pos == len(cursor.typable_text) -1:
                    collat_cursor.at_end = True
                    collat_cursor.current_errors += 1
                    cursor.current_errors += 1

                collat_cursor.update_context()

                if collat_cursor.prev_char == '\n':
                    collat_cursor.line += 1
                    collat_cursor.line_pos = 0

                collat_cursor.draw(collat_cursor.char)

            elif collat_cursor and not collat_cursor.at_end:
                self.collateral_error_count += 1
                if collat_cursor.char == '\n':
                    collat_cursor.line += 1
                    collat_cursor.line_pos = 0
                    
                else:
                    collat_cursor.line_pos += 1

                collat_cursor.text_pos += 1
                collat_cursor.current_errors += 1
                collat_cursor.draw(collat_cursor.next_char)
            
            if cursor.at_end:
                cursor.current_errors = 1
            elif (not collat_cursor) or (collat_cursor and not collat_cursor.at_end):
                cursor.current_errors += 1

        return

    def pause(self, event):
        self.last_keypress = None
        self.cursor.color = 'orange'
        self.cursor.draw(self.cursor.char)

    def end_session(self):
        filename = self.main.title()
        self.main.destroy()
        self.main = None

        #find last line number and update user_data.txt
        data = get_data(filename)
        num_lines = self.cursor.line+1 if self.cursor.line+1 < data['segment_size'] else data['segment_size']
        line_no = data['line_no'] + (num_lines)
        line_data = [filename, {'key': 'line_no','value': line_no}]
        save_data(line_data, line=2)
        save_data(self.key_profiles, line=3)
        
        tc = len(self.cursor.typable_text)
        cps = 1/(self.time_taken/tc)
        wpm = round(cps/5*60)
        mins = int(self.time_taken/60)
        secs = round(self.time_taken % 60)
        ukp = (self.error_count + self.collateral_error_count + self.backspace_count) / tc
        best_key = '0'
        worst_key = '0'
        for char in self.key_profiles.keys():
            if self.key_profiles[char]['correct'] > self.key_profiles[best_key]['correct']:
                best_key = char
        
        for char in self.key_profiles.keys():
            if self.key_profiles[char]['incorrect'] > self.key_profiles[best_key]['incorrect']:
                worst_key = char
        summary = f'''
        
Total Characters: {tc}
Time taken: {mins}:{secs:0>2}
Wpm: {wpm}
Errors: {self.error_count}
Keys type collaterally before backspacing: {self.collateral_error_count}
Backspaces: {self.backspace_count}
Unproductive keystrokes: {ukp:.0%}
Best key: {best_key}
Worst key: {worst_key}
'''
        print(summary)


class Cursor:
    def __init__(self, main, x=20, y=10, char=None, page=None, color='green', width = resources.CURSOR['width'], height = resources.CURSOR['height'], text = None):
        self.main = main
        self.Page = page
        self.tab_size = 4
        self.in_tab, self.at_end, self.from_backspace = [False]*3
        self.startpos = (x,y)
        self.displayed_text = text
        self.typable_text = ''.join([line.lstrip(' ') for line in text.splitlines(keepends=True)])
        self.prev_char, self.char, self.next_char = None, char, None
        self.line, self._line_pos, self.line_pos, self.text_pos, self.current_errors = [0]*5
        self.width, self.height, self.color = width, height, color
        self.style = {'font': 'courier 10', 'justify': 'left', 'bg': self.color, 'fg': 'white'}

        self.Frame = tk.Frame(self.main, bg=self.color)
        self.Frame.place(x = self.x, y = self.y, width=self.width, height=self.height)
        self.char_label = tk.Label(self.Frame, text=self.char, **self.style)
        self.char_label.place(x=-3,y=-5)
        return


    @property
    def x(self):
        return self.line_pos * self.width + self.startpos[0]


    @property
    def y(self):
        return self.line * (self.height + 2) + self.startpos[1]


    @property
    def line_pos(self):
        return self._line_pos

    @line_pos.setter
    def line_pos(self, arg):
        if arg != 0:
            self._line_pos = arg
        else:
            try:
                line = self.displayed_text.splitlines()[self.line]
                if self.next_char == '\n':
                    self._line_pos = len(line)
                else:
                    self._line_pos = line.find(line.lstrip()[0])
            except IndexError:
                self._line_pos = 0


    def update_context(self):
        text = self.typable_text
        if not self.at_end:
            self.prev_char = text[self.text_pos-1]
            self.char = text[self.text_pos]
            self.next_char = text[self.text_pos+1]
        else: 
            self.prev_char = text[self.text_pos-1]
            self.char = text[self.text_pos]
        return 


    def draw(self, char):
        width = self.width
        if char == '\n':
            char = '⏎'
            width = self.width * 1.5

        if self.main and self.at_end and self.color == 'green':
            self.Page.end_session()

        elif self.main:
            self.char = char
            self.Frame.place(x=self.x,y=self.y, width=width, height=self.height)
            self.char_label.config(text=self.char, bg=self.color)

        return




if __name__ == '__main__':
    os.chdir(resources.data_folder) 
    # ^ ensures that app launches as long as resources.py, main.py, and user_data.txt are in the same folder, regardless of what directory main.py is run from (if launched by file explorer or command prompt)
    os.system('type main.py > sample.txt')
    app = App()
    app.run()