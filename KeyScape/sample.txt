from importlib import reload
import tkinter as tk
import tkinter.messagebox as mb
import os
import resources 
import time

# TO FIX: practicepage skips a line when moving onto next segment after completing current segment
#---------------------------------NOTEPAD---------------------------------------
#practice idea: use network ports and another client application to view typing
#practice sessions in real time

#prevent more than one practice page being opened simultaneously

#add buttons to practice pages to navigate text segments

#add analytics system
#-------------------------------------------------------------------------------

def track_time(func):
    def wrapper(self, *args, **kwargs):
        char = args[0].keysym
        if char not in resources.NONE_TYPABLES+['BackSpace'] and not self.in_tab:
            stop = time.monotonic()
            start = self.Page.last_keypress if self.Page.last_keypress else stop
            self.Page.time_taken += (stop-start)
            self.Page.last_keypress = stop
        func(self, *args, **kwargs)
        return 
    return wrapper

def save_data(filename, data: dict):
    '''
    data -> [index, new_value]
    index = index of data in tuple in format (line number, number of lines per segment)
    '''

    with open(resources.data_filename, 'r+',encoding="UTF-8") as file:
        filenames, s_data = [eval(line) for line in file.readlines()]
        index = filenames.index(filename)
        s_data[index][data['name']] = data['new_data']
        file_data = repr(filenames) + "\n" + repr(s_data)
        file.seek(0)
        file.writelines(file_data)
        file.truncate()
    reload(resources)

def get_data(filename):
    with open(resources.data_filename) as file:
        filenames, s_data = [eval(line) for line in file.readlines()]
        index = filenames.index(filename)
        return s_data[index]
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
            save_data(name, {'name': 'line_no', 'new_data': curr_line})
            selection = lines[curr_line:curr_line + resources.SAMPLE_SIZE]
            txt = ''.join(selection)
            self.CurrentPage = Page(name, txt) # fix this. too ambiguous           
        except IndexError:
            print('You have hit the end of the file.')
            restart = mb.askokcancel('lesson completed', "You have completed the lesson. Would you like restart?")
            if restart:
                save_data(name, {'name': 'line_no', 'new_data': 0})
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
                 geometry=f"{resources.WIN['width']}x{resources.WIN['height']}+{resources.WIN['x']}+{resources.WIN['y']}", 
                 name='typing_page', dimensions=(resources.WIN['min_width'],
                 resources.WIN['min_height'])):
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
        self.Cursor = Cursor(self.main, page=self, char=first_char, text=self.displayed_text)
        self.main.bind('<Key>', self.update_cursor)
        self.last_keypress = None
        self.curr_line = 0

    def display_text(self, txt: str, bg: str ='', fg: str ='black') -> str:
        WIN = resources.WIN
        CURSOR = resources.CURSOR
        max_length = max([len(l) for l in txt.splitlines()]) #get length of longest line in text
        x_pad = WIN['x_padding']
        y_pad = WIN['y_padding']
        bottom_pad = WIN['b_padding']
        c_width = CURSOR['width']
        c_height = CURSOR['height']
        new_wn_height = y_pad + (c_height + 2)*len(txt.splitlines()) + bottom_pad
        new_wn_width = x_pad*2 + c_width * max_length

        if new_wn_width < WIN['width']:
            wn_width = WIN['width']
        else:
            wn_width = new_wn_width
        if new_wn_height < WIN['height']:
            wn_height = WIN['height']
        else:
            wn_height = new_wn_height

        self.main.geometry(f'{wn_width}x{wn_height}')
        self.main.minsize(new_wn_width,new_wn_height)
        bg = self.main['bg'] if bg == '' else bg
        text = tk.Label(self.main, text=txt, font='courier 10', justify='left', bg=bg, fg=fg)
        text.place(x=x_pad,y=y_pad)
        return txt
    
    def update_cursor(self, event: tk.Event):
        self.Cursor.update(event)

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
        if char == '\n':
            char = '⏎'
        width = self.width * 1.5 if char == '⏎' else self.width

        if self.main and self.at_end and self.color == 'green':
            filename = self.main.title()
            self.main.destroy()
            self.main = None

            #find last line number and update user_data.txt
            data = get_data(filename)
            num_lines = self.line +1 if self.line+1 < data['segment_size'] else data['segment_size']
            line_no = data['line_no'] + (num_lines)
            save_data(filename, {'name': 'line_no','new_data': line_no})
            
            cps = 1/(self.Page.time_taken/len(self.typable_text))
            wpm = cps /5*60
            mins = int(self.Page.time_taken/60)
            secs = round(self.Page.time_taken % 60)

            print(len(self.typable_text))
            print(f"{mins}:{secs:0>2}")
            print("Wpm:", wpm)
        elif self.main:
            self.char = char
            self.Frame.place(x=self.x,y=self.y, width=width, height=self.height)
            self.char_label.config(text=self.char, bg=self.color)

        return

    @track_time
    def update(self, event):
        page = self.Page
        collat_cursor = page.collat_cursor
        disp_txt_lines = self.displayed_text.splitlines()
        for curs in [self, collat_cursor]:
            if curs and curs.text_pos == len(self.typable_text) -1:
                curs.at_end = True
                
        self.update_context()
        if collat_cursor:
            collat_cursor.update_context()
        
        if event.keysym in resources.NONE_TYPABLES:
            pass

        elif event.keysym == 'Tab':
            self.in_tab = True
            for i in range(self.tab_size):
                _event = tk.EventType.KeyPress
                _event.keysym = 'space'
                _event.char = ' '
                page.update_cursor(_event)
            self.in_tab = False

        elif event.char == self.char and self.current_errors == 0:
            self.color = 'green'
            self.from_backspace = False
            self.text_pos += 1
            self.line_pos += 1
            self.draw(self.next_char)

        elif event.char == '\r' and self.char == '\n' and self.current_errors == 0:
            self.color = 'green'
            self.line += 1
            self.line_pos = 0
            self.text_pos += 1
            self.draw(self.next_char)

        elif event.keysym == 'BackSpace':
            self.at_end = False
            if collat_cursor: collat_cursor.at_end = False
            if self.color == 'green' and self.text_pos > 0:
                self.line_pos -= 1
                self.text_pos -= 1
            elif self.color == 'red':
                self.current_errors -= 1
                self.from_backspace = True
                if collat_cursor: 
                    collat_cursor.current_errors -= 1

            if self.prev_char == '\n' and not page.collat_cursor and self.text_pos > 0 and not self.from_backspace:
                self.line -= 1
                self.line_pos = len(disp_txt_lines[self.line])

            if self.current_errors == 0:
                self.color = 'green'
                if self.text_pos == 0:
                    self.draw(self.typable_text[0])

                else:
                    self.draw(self.char if self.from_backspace and self.text_pos > 0 else self.prev_char)
                    self.from_backspace = False

            if self.current_errors > 0 and collat_cursor:
                if self.current_errors == 1:
                    collat_cursor.Frame.destroy()
                    page.collat_cursor = None
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
            if self.color == 'green':
                self.color = 'red'
                self.draw(self.char)
                
            
            if self.current_errors == 1 and not self.at_end:
                x = self.startpos[0]
                y = self.startpos[1]
                page.collat_cursor = Cursor(page.main, x=x, y=y, page=page, color='gray', text=page.displayed_text)
                collat_cursor = page.collat_cursor
                collat_cursor.text_pos = self.text_pos + 1
                collat_cursor.line = self.line
                collat_cursor.line_pos = self.line_pos + 1
                collat_cursor.current_errors = self.current_errors
                if collat_cursor.text_pos == len(self.typable_text) -1:
                    collat_cursor.at_end = True
                    collat_cursor.current_errors += 1
                    self.current_errors += 1

                collat_cursor.update_context()

                if collat_cursor.prev_char == '\n':
                    collat_cursor.line += 1
                    collat_cursor.line_pos = 0

                collat_cursor.draw(collat_cursor.char)

            elif collat_cursor and not collat_cursor.at_end:
                if collat_cursor.char == '\n':
                    collat_cursor.line += 1
                    collat_cursor.line_pos = 0
                    
                else:
                    collat_cursor.line_pos += 1

                collat_cursor.text_pos += 1
                collat_cursor.current_errors += 1
                collat_cursor.draw(collat_cursor.next_char)
            
            if self.at_end:
                self.current_errors = 1
            elif (not collat_cursor) or (collat_cursor and not collat_cursor.at_end):
                self.current_errors += 1

        return
    
if __name__ == '__main__':
    os.chdir(resources.data_folder) 
    # ^ ensures that app launches as long as resources.py, main.py, and user_data.txt are in the same folder, regardless of what directory main.py is run from (if launched by file explorer or command prompt)
    
    os.system('type main.py > sample.txt')

    app = App()
    app.run()