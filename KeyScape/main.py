#---------------------------------NOTEPAD---------------------------------------
# practice idea: use network ports and another client application to view typing
#                practice sessions in real time
# 
# improve app layout and graphic design
# 
# add a typo hotmap to metrics page
#
# add avg speed label to metrics page and change button name to 'Details' or 
# similar
# 
# add 'type a book' feature to scrape chapters from readnovelfull and insert 
# them into files to type
#-------------------------------------------------------------------------------


from importlib import reload
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as mb
import os
import resources 
import time
import string
import datetime
import matplotlib.pyplot as plt
import numpy as np


def reset_user_profile():
    err_profile = {}
    speed_data = {}
    for char in string.printable.replace('\r\x0b\x0c', ''):
        err_profile[char] = {'correct': 0, 'incorrect': 0}
    save_data(err_profile, line=3)
    save_data(speed_data, line=4)


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
    data -> [Dict] representing new data\n
    line -> [Int] representing number of line to write data to
    '''

    with open(resources.data_filename, 'r+',encoding="UTF-8") as file:
        filenames, user_data, err_profile, speed_data = [eval(l) for l in file.readlines()]
        content = [filenames, user_data, err_profile, speed_data]
        if line:
            content[line-1] = new_data
        else:
            content = new_data

        formula = ''
        for l in range(len(content)):
            formula += '{'+ f'{l}' + '}\n'
        content = formula.format(*content)[:-1]
        file.seek(0)
        file.write(content)
        file.truncate()
    reload(resources)


def get_data(line = None):
    if line:
        line -= 1
    with open(resources.data_filename, encoding='utf-8') as file:
        all_data = [eval(line) for line in file.readlines()]
        
    if line:
        return all_data[line]
    else:
        return all_data


def get_line_numbers(page, curr_line, amount):
    line_numbers = ''
    if page.kind == 'typing_page':
        for line in range(amount):
            line_numbers += f'{curr_line + line:2}\n'
    return line_numbers[:-1]


def get_selection(filename, curr_line):
    curr_line -= 1
    sources = resources.SOURCES
    sample_size = resources.USER_DATA['settings']['sample_size']
    lines = open(sources[filename], encoding="UTF-8").readlines()
    selection = ''
    while lines[curr_line].lstrip(' ') == '\n':
        curr_line -= 1
        selection = lines[curr_line - sample_size:curr_line]
    
    selection = lines[curr_line:curr_line + sample_size] if not selection else selection
    txt = ''.join(selection)
    txt = txt.replace('’',"'")
    for char in txt:
        if char not in string.printable.replace('\r\x0b\x0c', ''):
            txt = txt.replace(char, '')
    # Stop chaos from reigning(both symbols mean the same thing but are 
    # technically different characters and the first isn't found on 
    # keyboards, so it's impossible to type...)
    return (txt, curr_line+1)



class App:
    def __init__(self):
        self.current_pages = {}
        self.Home = HomePage('Home', app=self, kind='home_page')


    def run(self):
        return self.Home.main.mainloop()


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


    def destroy(self):
        self.Frame.destroy()
        del(self)
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

    @property
    def x(self):
        return self.line_pos * self.width + self.pos[0] +  + self.Page.lineLabel.winfo_width()

    @property
    def y(self):
        return self.line * (self.height + 2) + self.pos[1]


class Page:
    def __init__(self, title: str,  
                 app: App=None,
                 kind: str ='typing_page', 
                 geometry=f"{resources.WIN_CONFIG['width']}x{resources.WIN_CONFIG['height']}+{resources.WIN_CONFIG['x']}+{resources.WIN_CONFIG['y']}",
                 dimensions=(resources.WIN_CONFIG['min_width'],
                 resources.WIN_CONFIG['min_height'])):
        
        if title in app.current_pages:
            app.current_pages[title].main.deiconify()
            self.already_existed = True
            return
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
        self.main.focus_force()
        self.already_existed = False

        return
    

    def close(self):
        self.main.destroy()
        self.App.current_pages.pop(self.name)

        if self.kind == 'home_page':
            for page in list(self.App.current_pages.keys()):
                self.App.current_pages[page].close()
            
        elif self.kind == 'settings_page' and 'Home' in self.App.current_pages:
            self.App.current_pages['Home'].main.deiconify()
        

    def display_text(self, txt: str, bg: str ='', fg: str ='black') -> str:
        x_pad = resources.WIN_CONFIG['x_padding']
        y_pad = resources.WIN_CONFIG['y_padding']
        bg = bg or self.main['bg']
        label_x_pad = x_pad if not self.lineLabel else x_pad+self.lineLabel.winfo_width()
        
        self.scale_window(txt)
        self.textLabel = tk.Label(self.main, text=txt, font='courier 10', justify='left', bg=bg, fg=fg)
        self.textLabel.place(x=label_x_pad, y=y_pad)
        self.displayed_text = txt
        return


    def refresh(self):
        self.close()
        self.__init__(self.name, self.App, self.kind)


    def scale_window(self, txt):
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


class HomePage(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main.title('KeyScape')

        def get_typing_page_start_func(filename):
            def func():
                page = TypingPage(filename, app = self.App)
            return func

        def start_settings_page():
            page = SettingsPage('Settings', self.App, 'settings_page')

        def start_metrics_page():
            page = MetricsPage('Metrics', self.App, 'metrics_page')

        for filename in resources.SOURCES.keys():
            btn = ttk.Button(self.main, text=filename, command=get_typing_page_start_func(filename))
            btn.grid() # TODO: Fix appearance

        settings_btn = ttk.Button(self.main, text='Settings', command=start_settings_page)
        settings_btn.grid()

        metrics_page_btn = ttk.Button(self.main, text='Performance', command=start_metrics_page)
        metrics_page_btn.grid()
        return


class SettingsPage(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sample_size = tk.StringVar(self.main)
        sample_size_lbl = tk.Label(self.main, text='Sample Size: ')
        sample_size_eb = ttk.Entry(self.main, textvariable=self.sample_size, width=5, justify='center')
        sample_size_eb.bind('<Return>', func=self.save_settings)
        self.sample_size.set(str(resources.SAMPLE_SIZE))
        add_new_source_btn = ttk.Button(self.main, text='Add new source', command=self.start_source_addition_page)
        del_source_btn = ttk.Button(self.main, text='Remove source', command=self.start_source_removal_page)
        sample_size_lbl.pack()
        sample_size_eb.pack()
        add_new_source_btn.pack()
        del_source_btn.pack()


    def save_settings(self, event = None):
            new_size = min(int(self.sample_size.get()), resources.MAX_SAMPLE_SIZE)
            user_data = get_data(2)
            user_data['settings']['sample_size'] = new_size
            save_data(user_data, 2)
            self.close()


    def start_source_addition_page(self):
            def get_add_new_source_func(win, filepath):
                def func(event, win = win, filepath = filepath):
                    filepath = filepath.get()
                    filename = os.path.basename(filepath)
                    sources, user_data = resources.SOURCES, resources.USER_DATA
                    try: 
                        with open(filepath, encoding='utf-8') as file:
                            file.readlines()
                        sources[filename] = filepath
                        user_data['line_numbers'][filename] = 1
                        save_data(sources, line=1)
                        save_data(user_data, line=2)
                    except FileNotFoundError or FileExistsError:
                        msg = mb.Message(win.main, title='Invalid path', message='The path you have entered is invalid or we can\'t access that file.')
                        msg.show()

                    self.App.Home.refresh()
                return func

            win = Page('New Source', self.App, 'new_source_page')
            filepath = tk.StringVar(win.main)
            lbl = tk.Label(win.main, text='File path: ')
            entry = ttk.Entry(win.main, textvariable=filepath)
            entry.bind('<Return>', func=get_add_new_source_func(win, filepath))
            lbl.pack()
            entry.pack()
            entry.focus_force()


    def start_source_removal_page(self):
            def get_delete_source_func(win, filename):
                def func():
                    sources, user_data = resources.SOURCES, resources.USER_DATA
                    sources.pop(filename)
                    user_data['line_numbers'].pop(filename)
                    save_data(sources, line=1)
                    save_data(user_data, line=2)
                    self.App.Home.refresh()
                return func

            win = Page('Delete Source', self.App, 'rem_source_page')
            for source in resources.SOURCES:
                lbl = tk.Label(win.main, text=source+":")
                btn = ttk.Button(win.main, text='Delete', command=get_delete_source_func(win, source))
                lbl.pack()
                btn.pack()


class TypingPage(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.already_existed:
            return
        filename = self.name
        self.curr_line = resources.USER_DATA['line_numbers'][filename]
        curr_line = self.curr_line

        try:
            text, curr_line = get_selection(filename, curr_line)
            data = get_data(line=2)
            data['line_numbers'][filename] = curr_line
            save_data(data, line=2)
            for page in self.App.current_pages:
                if self.App.current_pages[page].name == filename: # Prevents duplicate windows
                    self.App.current_pages[page].main.deiconify()
                
            self.main.bind('<Key>', self.update)
            self.main.bind('<Motion>', self.pause)
            self.flips = 0
            self.initialize_variables()
            self.display_text(text)
            first_char = self.displayed_text.lstrip()[0]
            self.cursor = Cursor(self, char=first_char)

        except IndexError:
            restart = mb.askokcancel('lesson completed', "You have completed the lesson. Would you like restart?")
            if restart:
                data = get_data(line=2)
                data['line_numbers'][filename] = 1
                save_data(data, line=2)
                self.refresh()
            else:
                self.close()
                return


        def get_flip_page_func(turns=1):
            def flip_page(event = None):
                self.flips += turns
                curr_line = resources.USER_DATA['line_numbers'][filename]
                curr_line = get_selection(filename, curr_line)[1]
                target_line = min(curr_line, (curr_line - resources.SAMPLE_SIZE*self.flips))
                if target_line == curr_line:
                    self.flips = 0
                if target_line < 1:
                    target_line = 1
                    self.flips -= 1
                self.change_text(target_line)
            return flip_page
        
        btn_bar = tk.Frame(self.main)
        self.prev_btn = ttk.Button(btn_bar, text='Previous page', command=get_flip_page_func(), takefocus=False)
        self.next_btn = ttk.Button(btn_bar, text='Next page', command=get_flip_page_func(turns=-1), takefocus=False)
        curr_line = get_data(2)['line_numbers'][self.name]
        self.main.bind('<Left>', func=get_flip_page_func())
        self.main.bind('<Right>', func=get_flip_page_func(turns=-1))

        if curr_line != 1:
            self.prev_btn.pack(side='left', padx=15, pady=10)

        btn_bar.pack(side='bottom', fill='x')


    def change_text(self, starting_line):
        self.cursor.destroy()
        if self.collat_cursor:
            self.collat_cursor.destroy()
        txt, curr_line = get_selection(self.name, starting_line)
        
        self.next_btn.pack_forget() if self.flips == 0 else self.next_btn.pack(side='right', padx=15, pady=10)
        self.prev_btn.pack_forget() if curr_line == 1 else self.prev_btn.pack(side='left', padx=15, pady=10)
        
        num_lines = len(self.displayed_text.splitlines())
        line_numbers = get_line_numbers(self, curr_line, num_lines)
        self.initialize_variables()
        self.scale_window(txt)
        self.textLabel['text'] = txt
        self.lineLabel['text'] = line_numbers
        self.displayed_text = txt
        self.cursor = Cursor(self, char=txt.lstrip()[0])
        return


    def create_summary_page(self, perf_data):
        
        def close_orig_page(summary_page):
            def func(event=None):
                summary_page.close()
                self.App.current_pages[summary_page.original_page.name].close()
            return func
        
        def get_start_next_lesson_func(summary_page):
            def start_next_lesson(event=None):
                close_orig_page(summary_page)()
                next_lesson = TypingPage(self.name, self.App)
            return start_next_lesson

        def get_review_next_lesson_func(summary_page, target_line):
            def review_next_lesson(event=None):
                summary_page.close()
                self.change_text(target_line)
                self.flips -= 1
            return review_next_lesson
        
        summary = f'''
        
Total Characters: {perf_data['total_chars']}

Time taken: {perf_data['mins']}:{perf_data['secs']:0>2}

Wpm: {perf_data['wpm']}

Errors: {perf_data['errors']}

Keys type collaterally before backspacing: {perf_data['collat_errors']}

Backspaces: {perf_data['backspaces']}

Unproductive keystrokes: {perf_data['unprod_keystrokes']:.0%}

Best key: {perf_data['best_key']}

Worst key: {perf_data['worst_key']}
'''
        
        summary_page = Page('Summary', self.App, 'summary_page', "100x100+100+100")
        summary_page.original_page = self
        summary_page.display_text(summary)
        summary_page.main.protocol('WM_DELETE_WINDOW', close_orig_page(summary_page))
        btn = ttk.Button(summary_page.main, text="Next Lesson", command=get_start_next_lesson_func(summary_page))
        btn.pack(side='bottom', pady=10)
        summary_page.main.bind('<Return>', func=get_start_next_lesson_func(summary_page))
        summary_page.main.bind('<Escape>',func= close_orig_page(summary_page))

        if self.flips != 0:
            
            target_line = int(self.lineLabel['text'][:2]) + resources.SAMPLE_SIZE
            summary_page.main.bind('<Right>', func=get_review_next_lesson_func(summary_page, target_line))


    def display_text(self, txt, *args, bg='', fg='black', **kwargs) -> str:
        x_pad = resources.WIN_CONFIG['x_padding']
        y_pad = resources.WIN_CONFIG['y_padding']
        bg = bg or self.main['bg']
        curr_line = resources.USER_DATA['line_numbers'][self.name]
        num_lines = len(txt.splitlines())
        line_numbers = get_line_numbers(self, curr_line, num_lines)
        self.lineLabel = tk.Label(self.main, text=line_numbers, font='courier 10', justify='left', bg=bg, fg='grey')
        self.lineLabel.place(x=x_pad, y=y_pad)
        self.lineLabel.update()
        return super().display_text(txt,bg, fg, *args, **kwargs)


    def end_session(self):
        total_chars = len(self.cursor.typable_text)
        chars_per_second = 1/(self.time_taken/total_chars)
        wpm = round(chars_per_second/5*60)
        mins = int(self.time_taken/60)
        secs = round(self.time_taken % 60)
        ukp = (self.error_count + self.collateral_error_count + self.backspace_count) / total_chars

        #find last line number and update user_data.txt
        user_data = get_data(line=2)
        speed_data = get_data(line=4)
        lines_typed = min((self.cursor.line+1), user_data['settings']['sample_size'])

        date = datetime.datetime.today().toordinal()
        if date in speed_data:
            avg_wpm = round((speed_data[date]+ wpm)/2)
        else:
            avg_wpm = wpm
        speed_data[date] = avg_wpm
        save_data(speed_data, line=4)

        if self.flips == 0:
            self.main.bind('<Key>', func=lambda event: 1+1) # makes it impossible to type anything else
            user_data['line_numbers'][self.name] += (lines_typed)
            save_data(user_data, line=2)

        save_data(self.key_profiles, line=3)
        
        

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
        
        performance_data = {
            'total_chars': total_chars,
            'mins': mins,
            'secs': secs,
            'wpm': wpm,
            'errors': self.error_count,
            'collat_errors': self.collateral_error_count,
            'backspaces': self.backspace_count,
            'unprod_keystrokes': ukp,
            'best_key': best_key,
            'worst_key': worst_key,
        }
        
        self.create_summary_page(performance_data)


    def initialize_variables(self):
        self.time_taken = 0
        self.collat_cursor = None
        self.displayed_text = None
        self.last_keypress = None
        self.curr_line = 0
        self.error_count = 0
        self.backspace_count = 0
        self.collateral_error_count = 0
        self.key_profiles = get_data(line=3)
        return


    def pause(self, event):
        try:
            self.last_keypress = None
            self.cursor.color = 'orange'
            self.cursor.draw(self.cursor.char)
        except AttributeError:
            pass

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
                _event = ttk.EventType.KeyPress
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


class MetricsPage(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main.title('Performance')
        speed_btn = ttk.Button(self.main, text='Speed Overview', command=self.show_speed_graph)
        speed_btn.grid()

        accuracy_btn = ttk.Button(self.main, text='Accuracy Overview', command=self.show_accuracy_graph)
        accuracy_btn.grid()


    def get_close_graph_func(self, fig):
        def close(event):
            if event.key == 'escape':
                plt.close(fig)
        return close
    

    def show_speed_graph(self):
        def update_annot(ind):
            x,y   = line.get_data()
            annot.xy = (x[ind['ind'][0]], y[ind['ind'][0]])
            text = f"{str(y[ind['ind'][0]])} wpm, {x[ind['ind'][0]]}" 
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.4)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                cont, ind = line.contains(event)
                if cont:
                    update_annot(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

        data = get_data(line=4)
        x = [datetime.datetime.fromordinal(x).strftime("%b %d, %Y") for x in data.keys()]
        x.sort()
        y = [data[datetime.datetime.strptime(d, "%b %d, %Y").toordinal()] for d in x]
        if len(x) == 0:
            m = mb.Message(self.main, title="No data stored", message="Complete a lesson to review your performance")
            m.show()
            return
        fig, ax = plt.subplots()
        fig.canvas.manager.set_window_title('Typing Speed Overview')
        line = plt.plot(x, y, 'o-')[0]
        plt.yticks(range(min(y), max(y)+1, 1))
        plt.xlabel('Date')
        plt.ylabel('Words Per Minute')
        plt.suptitle('Speed Overview (Avg speed per day)')
        annot = ax.annotate('', (0,0), xytext=(-20,20),textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        fig.canvas.mpl_connect("motion_notify_event", hover)
        fig.canvas.mpl_connect('key_release_event', self.get_close_graph_func(fig))
        plt.show()

        
    def show_accuracy_graph(self):
        def update_annot(ind):
            pos = sc.get_offsets()[ind["ind"][0]]
            annot.xy = pos
            text = f"{str(y[ind['ind'][0]])}%, {x[ind['ind'][0]]}" 
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.4)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                cont, ind = sc.contains(event)
                if cont:
                    update_annot(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()

        data = get_data(line=3)
        data.pop('\t')
        data.pop('\n')

        x = list(data.keys())
        y = []
        for key in x.copy():
            try:
                inc = data[key]['incorrect']
                cor = data[key]['correct']
                if cor == 0 and inc == 0:
                    x.remove(key)
                else:
                    score = (cor/(cor+inc))*100
                    y.append(round(score, 1))
            except ZeroDivisionError:
                y.append(0)

        if len(x) == 0:
            m = mb.Message(self.main, title="No data stored", message="Complete a lesson to review your performance")
            m.show()
            return

        fig, ax = plt.subplots()
        fig.canvas.manager.set_window_title('Accuracy Overview')
        fig.set_figwidth(15)
        fig.subplots_adjust(left=0.07, right=0.955)
        plt.yticks(np.arange(0, max(y)+1, 10))
        plt.xlabel('Key')
        plt.ylabel('Accuracy Rate (%)')
        plt.suptitle('Key Accuracy Overview')
        sc = plt.scatter(x, y)
        annot = ax.annotate("", xy=(0,0), xytext=(-20,20),textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        fig.canvas.mpl_connect("motion_notify_event", hover)
        fig.canvas.mpl_connect('key_release_event', self.get_close_graph_func(fig))
        plt.show()


    def close(self, *args, **kwargs):
        super().close(*args, **kwargs)
        plt.close('all')
    


if __name__ == '__main__':
    os.chdir(resources.data_folder) 
    # ^ ensures that app launches as long as resources.py, main.py, and user_data.txt are in the same folder, regardless of what directory main.py is run from (if launched by file explorer or command prompt)
    reset_user_profile()
    os.system('type main.py > sample.txt')
    app = App()
    app.run()