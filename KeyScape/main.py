#---------------------------------NOTEPAD---------------------------------------
# practice idea: use network ports and another client application to view typing
#                practice sessions in real time
# 
# add a way to remove sources from app to settings page
#
# improve app layout and graphic design
# 
# create link to a key accuracy graph on home page
# 
# add 'type a book' feature to scrape chapters from readnovelfull and insert 
# them into files to type
#-------------------------------------------------------------------------------


from importlib import reload
import tkinter as tk
import tkinter.messagebox as mb
import os
import resources 
import time
import string


def reset_user_profile():
    with open(resources.data_filename, 'r+', encoding='utf-8') as file:
        fnames, l_data, profile = [eval(line) for line in file.readlines()]
        for char in string.printable.replace('\r\x0b\x0c', ''):
            profile[char] = {'correct': 0, 'incorrect': 0}
        content = f'{fnames}\n{l_data}\n{profile}'
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


def save_data(new_data, line=None):
    '''
    data -> [index, new_value]
    index = index of data in tuple in format (line number, number of lines per segment)
    '''

    with open(resources.data_filename, 'r+',encoding="UTF-8") as file:
        filenames, user_data, err_profile = [eval(l) for l in file.readlines()]
        content = [filenames, user_data, err_profile]
        if line:
            content[line-1] = new_data
        else:
            content = new_data
        content = '{0}\n{1}\n{2}'.format(*content)
        file.seek(0)
        file.write(content)
        file.truncate()
    reload(resources)


def get_data(line = None):
    if line:
        line -= 1
    with open(resources.data_filename, encoding='utf-8') as file:
        filenames, user_data, err_profile = [eval(line) for line in file.readlines()]
        
    if line:
        return [filenames, user_data, err_profile][line]
    else:
        return [filenames, user_data, err_profile]


def get_line_numbers(page, curr_line):
    line_numbers = ''
    if page.kind == 'typing_page':
        for line in range(resources.SAMPLE_SIZE):
            line_numbers += f'{curr_line + line:2}\n'
    return line_numbers[:-1]


def get_selection(filename, curr_line, direction=''):
    curr_line -= 1
    sources = resources.SOURCES
    sample_size = resources.EDITOR_DATA['settings']['sample_size']
    lines = open(sources[filename], encoding="UTF-8").readlines()
    selection = ''
    while lines[curr_line].lstrip(' ') == '\n':
        curr_line -= 1
        selection = lines[curr_line - sample_size:curr_line]
    
    selection = lines[curr_line:curr_line + sample_size] if not selection else selection
    txt = ''.join(selection)
    txt = txt.replace('’',"'")
    # Stop chaos from reigning(both symbols mean the same thing but are 
    # technically different characters and the first isn't found on 
    # keyboards, so it's impossible to type...)
    return (txt, curr_line+1)


class App:
    def __init__(self):
        self.current_pages = {}
        self.Home = Page('Home', app=self, kind='home_page')
        self.Home.main.title('KeyScape')
        self.setup_homepage(self.Home)
        self.current_pages['Home'] = self.Home
        return
    

    def setup_homepage(self, page):
        def get_command_func(filename):
            def func():
                self.create_typing_page(filename)
            return func
        for filename in resources.SOURCES.keys():
            btn = tk.Button(page.main, text=filename, command=get_command_func(filename))
            btn.grid() # TODO: Fix appearance
        settings_btn = tk.Button(page.main, text='Settings', command=self.start_settings_page)
        settings_btn.grid()
        return
    

    def start_settings_page(self):
        def save_settings(event):
            user_data = get_data(2)
            user_data['settings']['sample_size'] = int(sample_size.get())
            save_data(user_data, 2)
            settings_page.close()
            
        
        def start_source_addition_page():
            def get_add_new_source_func(win, filepath):
                def func(event, win = win, filepath = filepath):
                    filepath = filepath.get()
                    filename = os.path.basename(filepath)
                    names, user_data, err_profile = get_data()
                    try: 
                        with open(filepath) as file:
                            file.readlines()
                        names[filename] = filepath
                        user_data['line_numbers'][filename] = 1
                        new_data = [names, user_data, err_profile]
                        save_data(new_data)
                    except FileNotFoundError or FileExistsError:
                        msg = mb.Message(win.main, title='Invalid path', message='The path you have entered is invalid or we can\'t access that file.')
                        msg.show()
                    
                    win.close()
                    self.Home.close()
                    self.__init__()
                    self.Home.main.focus_force()
                return func

            win = Page('New Source', self, 'new_source_page')
            filepath = tk.StringVar(win.main)
            lbl = tk.Label(win.main, text='File path: ')
            entry = tk.Entry(win.main, textvariable=filepath)
            entry.bind('<Return>', func=get_add_new_source_func(win, filepath))
            lbl.pack()
            entry.pack()
            entry.focus_force()

        settings_page = Page('Settings', app=self, kind='settings_page')
        sample_size = tk.StringVar(settings_page.main)
        sample_size_lbl = tk.Label(settings_page.main, text='Sample Size: ')
        sample_size_eb = tk.Entry(settings_page.main, textvariable=sample_size, width=5, justify='center')
        sample_size_eb.bind('<Return>', func=save_settings)
        sample_size.set(str(resources.SAMPLE_SIZE))
        new_source_btn = tk.Button(settings_page.main, text='Add new source', command=start_source_addition_page)
        sample_size_lbl.pack()
        sample_size_eb.pack()
        new_source_btn.pack()


    def initialize_typing_page(self, page):
        page.time_taken = 0
        page.collat_cursor = None
        page.displayed_text = None
        page.last_keypress = None
        page.curr_line = 0
        page.error_count = 0
        page.backspace_count = 0
        page.collateral_error_count = 0
        page.key_profiles = get_data(line=3)
        return
    

    def create_typing_page(self, filename: str):
        self.curr_line = resources.EDITOR_DATA['line_numbers'][filename]
        curr_line = self.curr_line

        try:
            txt, curr_line = get_selection(filename, curr_line)
            data = get_data(line=2)
            data['line_numbers'][filename] = curr_line
            save_data(data, line=2)
            for page in self.current_pages:
                if self.current_pages[page].name == filename: # Prevents duplicate windows
                    self.current_pages[page].main.deiconify()
                    return
                
            new_page = Page(filename, app=self)
            new_page.main.bind('<Key>', new_page.update)
            new_page.main.bind('<Motion>', new_page.pause)
            new_page.flips = 0
            self.initialize_typing_page(new_page)
            self.setup_typing_page(new_page, txt)
            new_page.main.focus_force()

        except IndexError:
            restart = mb.askokcancel('lesson completed', "You have completed the lesson. Would you like restart?")
            if restart:
                data = get_data(line=2)
                data['line_numbers'][filename] = 1
                save_data(data, line=2)
                self.create_typing_page(filename)
                return
            
        return
    

    def setup_typing_page(self, page, text):
        page.display_text(text)
        first_char = text.lstrip()[0]
        page.cursor = Cursor(page, char=first_char)

        filename = page.name
        
        def get_flip_page_func(page, turns=1):
            def flip_page(event = None):
                page.flips += turns
                curr_line = resources.EDITOR_DATA['line_numbers'][filename]
                curr_line = get_selection(filename, curr_line)[1]
                target_line = min(curr_line, (curr_line - resources.SAMPLE_SIZE*page.flips))
                if target_line == curr_line:
                    page.flips = 0
                if target_line < 1:
                    target_line = 1
                    page.flips -= 1
                self.change_typing_page(page, target_line)
            return flip_page
        
        btn_bar = tk.Frame(page.main)
        page.prev_btn = tk.Button(btn_bar, text='Previous page', command=get_flip_page_func(page), takefocus=False)
        page.next_btn = tk.Button(btn_bar, text='Next page', command=get_flip_page_func(page, turns=-1), takefocus=False)
        curr_line = get_data(2)['line_numbers'][page.name]
        page.main.bind('<Left>', func=get_flip_page_func(page))
        page.main.bind('<Right>', func=get_flip_page_func(page, turns=-1))

        if curr_line != 1:
            page.prev_btn.pack(side='left', padx=15, pady=10)

        btn_bar.pack(side='bottom', fill='x')


    def change_typing_page(self, page, line_no):
        page.cursor.destroy()
        if page.collat_cursor:
            page.collat_cursor.destroy()
        txt, curr_line = get_selection(page.name, line_no)
        
        page.next_btn.pack_forget() if page.flips == 0 else page.next_btn.pack(side='right', padx=15, pady=10)
        page.prev_btn.pack_forget() if curr_line == 1 else page.prev_btn.pack(side='left', padx=15, pady=10)
        
        line_numbers = get_line_numbers(page, curr_line)
        self.initialize_typing_page(page)

        page.textLabel['text'] = txt
        page.lineLabel['text'] = line_numbers
        page.displayed_text = txt
        page.cursor = Cursor(page, char=txt.lstrip()[0])


    def run(self):
        return self.Home.main.mainloop()


class Page:
    def __init__(self, title: str,  
                 app: App =None,
                 kind: str ='typing_page', 
                 geometry=f"{resources.WIN_CONFIG['width']}x{resources.WIN_CONFIG['height']}+{resources.WIN_CONFIG['x']}+{resources.WIN_CONFIG['y']}",
                 dimensions=(resources.WIN_CONFIG['min_width'],
                 resources.WIN_CONFIG['min_height'])):
        
        main = tk.Tk(kind)
        main.title(title)
        main.minsize(*dimensions)
        main.geometry(geometry)
        main.protocol('WM_DELETE_WINDOW', self.close)
        self.main = main
        self.name = title
        self.kind = kind
        self.textLabel, self.lineLabel = None, None
        self.App = app
        self.App.current_pages[self.name] = self
        self.main.bind('<Escape>', lambda event: self.close())

        return
    

    def display_text(self, txt: str, bg: str ='', fg: str ='black') -> str:
        
        WIN_CONFIG = resources.WIN_CONFIG
        CURSOR = resources.CURSOR
        txt_lines = txt.splitlines()
        max_length = max([len(line) for line in txt_lines])
        x_pad = WIN_CONFIG['x_padding']
        y_pad = WIN_CONFIG['y_padding']
        bottom_pad = WIN_CONFIG['bottom_padding']
        c_width = CURSOR['width']
        c_height = CURSOR['height']
        new_wn_height = y_pad + (c_height + 2)*len(txt_lines) + bottom_pad
        new_wn_width = x_pad*2 + c_width * (max_length + 4)
        wn_width = max([new_wn_width, WIN_CONFIG['width']])
        wn_height = max([new_wn_height, WIN_CONFIG['height']])

        self.main.geometry(f'{wn_width}x{wn_height}')
        self.main.minsize(new_wn_width, new_wn_height)
        bg = self.main['bg'] if bg == '' else bg
        if self.kind == 'typing_page':
            curr_line = resources.EDITOR_DATA['line_numbers'][self.name]
            line_numbers = get_line_numbers(self, curr_line)
            self.lineLabel = tk.Label(self.main, text=line_numbers, font='courier 10', justify='left', bg=bg, fg='grey')
            self.lineLabel.place(x=x_pad, y=y_pad)
            self.lineLabel.update()

        if not self.textLabel:
            self.textLabel = tk.Label(self.main, text=txt, font='courier 10', justify='left', bg=bg, fg=fg)
        
        label_x_pad = x_pad if not self.lineLabel else x_pad+self.lineLabel.winfo_width()
        self.textLabel.place(x=label_x_pad, y=y_pad)
        self.displayed_text = txt
        return

    @track_time
    def update(self, event):
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
            key_profiles[cursor.char]['correct'] += 1
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
                cursor.current_errors -= 1
                cursor.from_backspace = True
                if collat_cursor: 
                    collat_cursor.current_errors -= 1
                cursor.draw(cursor.char)

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
                x,y = cursor.pos
                self.collat_cursor = Cursor(self, x=x, y=y, color='gray')
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
        try:
            self.last_keypress = None
            self.cursor.color = 'orange'
            self.cursor.draw(self.cursor.char)
        except AttributeError:
            pass


    def end_session(self):
        #find last line number and update user_data.txt
        data = get_data(line=2)
        lines_typed = min((self.cursor.line+1), data['settings']['sample_size'])
        if self.flips == 0:
            self.main.bind('<Key>', func=lambda event: 1+1) # makes it impossible to type anything else
            data['line_numbers'][self.name] += (lines_typed)
            save_data(data, line=2)
        save_data(self.key_profiles, line=3)
        
        tc = len(self.cursor.typable_text)
        cps = 1/(self.time_taken/tc)
        wpm = round(cps/5*60)
        mins = int(self.time_taken/60)
        secs = round(self.time_taken % 60)
        ukp = (self.error_count + self.collateral_error_count + self.backspace_count) / tc

        #possible function below?
        keys = list(self.key_profiles.keys())
        keys.remove(' ')
        best_key = '0'
        worst_key = '0'
        scores = {}
        perfect_scores = 0
        bottom_scores = 0
        for char in keys:
                incorrect = self.key_profiles[char]['incorrect']
                correct = self.key_profiles[char]['correct']
                try:
                    if incorrect == 0:
                        scores[char] = 1
                        perfect_scores += 1
                    else:
                        scores[char] = 1 - incorrect/correct
                except ZeroDivisionError:
                    scores[char] = 0
                    bottom_scores += 1
        
        if perfect_scores > 1:
            best_key = '0'
            best_score = 0
            for key in scores:
                if scores[key] == 1:
                    score = self.key_profiles[key]['correct']
                    if score > best_score:
                        best_key = key
                        best_score = score
        else:
            for key in scores:
                if scores[key] > scores[best_key]:
                    best_key = key

        if bottom_scores > 1:
            worst_key = '0'
            worst_score = scores['0']
            for key in scores:
                if scores[key] == 0:
                    score = self.key_profiles[key]['incorrect']
                    if score < worst_score:
                        worst_key = key
                        worst_score = score
        else:
            for key in scores:
                if scores[key] < scores[worst_key]:
                    worst_key = key
        

        for key in best_key, worst_key:
            if key == '\n':
                key = 'Enter'
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
        self.create_summary_page(summary)


    def create_summary_page(self, summary):
        
        def close_orig_page(summary_page):
            def func(event=None):
                summary_page.close()
                self.App.current_pages[summary_page.original_page.name].close()
            return func
        
        def get_start_next_lesson_func(summary_page):
            def start_next_lesson(event=None):
                close_orig_page(summary_page)()
                self.App.create_typing_page(self.name)
            return start_next_lesson

        def get_review_next_lesson_func(summary_page, target_line):
            def review_next_lesson(event=None):
                summary_page.close()
                self.App.change_typing_page(self, target_line)
                self.flips -= 1
            return review_next_lesson
        
        
        summary_page = Page('Summary', self.App, 'summary_page', "100x100+100+100")
        summary_page.original_page = self
        summary_page.display_text(summary)
        summary_page.main.protocol('WM_DELETE_WINDOW', close_orig_page(summary_page))
        summary_page.main.focus_force()
        btn = tk.Button(summary_page.main, text="Next Lesson", command=get_start_next_lesson_func(summary_page))
        btn.pack(side='bottom', pady=10)
        summary_page.main.bind('<Return>', func=get_start_next_lesson_func(summary_page))
        summary_page.main.bind('<Escape>',func= close_orig_page(summary_page))

        if self.flips != 0:
            
            target_line = int(self.lineLabel['text'][:2]) + resources.SAMPLE_SIZE
            summary_page.main.bind('<Right>', func=get_review_next_lesson_func(summary_page, target_line))


    def close(self):
        self.main.destroy()
        self.App.current_pages.pop(self.name)

        if self.kind == 'home_page':
            for page in list(self.App.current_pages.keys()):
                self.App.current_pages[page].close()
            
        elif self.kind == 'settings_page' and 'Home' in self.App.current_pages:
            self.App.current_pages['Home'].main.deiconify()


class Cursor:
    def __init__(self, page, x=20, y=10, char=None, color='green', width = resources.CURSOR['width'], height = resources.CURSOR['height']):
        self.main = page.main
        self.Page = page
        self.tab_size = 4
        self.in_tab, self.at_end, self.from_backspace = [False]*3
        self.pos = (x,y)
        self.displayed_text = self.Page.displayed_text
        self.typable_text = ''.join([line.lstrip(' ') for line in self.displayed_text.splitlines(keepends=True)])
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
        return self.line_pos * self.width + self.pos[0] +  + self.Page.lineLabel.winfo_width()

    @property
    def y(self):
        return self.line * (self.height + 2) + self.pos[1]

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


    def destroy(self):
        self.Frame.destroy()
        del(self)
        return



if __name__ == '__main__':
    os.chdir(resources.data_folder) 
    # ^ ensures that app launches as long as resources.py, main.py, and user_data.txt are in the same folder, regardless of what directory main.py is run from (if launched by file explorer or command prompt)
    os.system('type main.py > sample.txt')
    app = App()
    app.run()