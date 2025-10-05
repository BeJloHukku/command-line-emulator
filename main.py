import tkinter as tk
from tkinter import *
import os
from datetime import datetime
import platform
import xml.etree.ElementTree as ET
from pathlib import Path
import re

def get_names():
    username = os.getlogin()  # получение имени пользователя
    hostname = platform.node()  # получение имени хоста
    return username, hostname

class Emulator:
    def __init__(self, root, vfs=None, start_scr=None):
        self.root = root
        if vfs:
            self.vfs = vfs  # получаем vfs из параметра
        else:
            self.vfs = os.path.expanduser("~\Desktop\KFG\Barinov\\vfs_data\.my_vfs\\vfs1.xml")
        self.start_scr = start_scr  # получаем стартовый скрипт из параметра
        self.current_dir = ''  # текущая директория
        self.virtual_env = {
            'HOME': '/',
            'PWD': '/',
        }
        # вывод параметров
        print("Параметры эмулятора")
        print("VFS - " + self.vfs)
        print("Start Script - " + (self.start_scr if self.start_scr else "None"))
        
        self.username, self.hostname = get_names()  # получаем имя пользователя и хоста
        self.root.title("Эмулятор - " + self.username + "@" + self.hostname)  # указываем их в заголовке окна
        
        # Создание интерфейса
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.command_entry = tk.Entry(self.input_frame, width=80)  # поле для ввода команд
        self.command_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.command_entry.bind("<Return>", self.read_com)  # Привязка Enter к обработке
        
        self.prompt_label = tk.Label(self.input_frame, text="Введите команду", width=20)
        self.prompt_label.pack()
        
        self.but_frame = tk.Frame(root)
        self.but_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.enter_but = tk.Button(self.but_frame, text="Выполнить команду", width=20, pady=5, command=self.read_com)  # кнопка для ввода команды
        self.enter_but.pack(side=tk.LEFT, fill=tk.BOTH)
        
        self.output_frame = tk.Frame(root)  # окно для вывода сообщений программы
        self.output_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.output_text = tk.Text(self.output_frame)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Инициализация VFS и скрипта
        self.start_vfs()
        if self.start_scr and os.path.exists(self.start_scr):
            self.start_script_run()  # если в системе есть стартовый скрипт, запускаем его
        elif self.start_scr:
            self.text_out(f"error: startup script not found: {self.start_scr}")  # иначе выводится ошибка

    def expand_vars(self, text):
        """Заменяет $VAR и ${VAR} на значения из VFS"""
        def replace(match):
            var_name = match.group(1) or match.group(2)
            return self.virtual_env.get(var_name, '')  # Только виртуальные переменные
        
        return re.sub(r'\$(\w+)|\$\{(\w+)\}', replace, text)
    

    def start_vfs(self):
        """Загрузка виртуальной файловой системы из XML"""
        try:
            if not os.path.exists(self.vfs):
                self.text_out(f"VFS NOT FOUND: {self.vfs}")
                self.vfs_tree = None
                self.vfs_files = []
                return
                
            # Парсим XML файл
            self.vfs_tree = ET.parse(self.vfs)
            self.vfs_root = self.vfs_tree.getroot()
            
            # Собираем все файлы и директории в плоский список
            self.vfs_files = []
            self._collect_files(self.vfs_root, "")
            
            print("Структура VFS:")
            for file_path in self.vfs_files:
                print(f"File: {file_path}")
                
        except Exception as e:
            print(f"Ошибка при загрузке VFS: {e}")
            self.vfs_tree = None
            self.vfs_files = []
            self.text_out("VFS NOT FOUND")

    def _collect_files(self, element, current_path):
        """Рекурсивный сбор всех файлов и папок из XML"""
        for child in element:
            if child.tag == 'directory':
                dir_name = child.get('name', '')
                dir_path = current_path + dir_name + '/'
                self.vfs_files.append(dir_path)  # добавляем саму директорию
                self._collect_files(child, dir_path)  # рекурсивно обходим содержимое
            elif child.tag == 'file':
                file_name = child.get('name', '')
                file_path = current_path + file_name
                self.vfs_files.append(file_path)

    def _find_element(self, path):
        """Поиск элемента в XML по пути"""
        if not self.vfs_tree:
            return None
            
        parts = path.rstrip('/').split('/')
        if not parts or parts == ['']:
            return self.vfs_root
            
        current = self.vfs_root
        for part in parts:
            found = False
            for child in current:
                if child.tag in ['directory', 'file'] and child.get('name') == part:
                    current = child
                    found = True
                    break
            if not found:
                return None
        return current

    def text_out(self, s):
        self.output_text.insert(tk.END, s + "\n")  # функция вывода результатов на экран
        self.output_text.see(tk.END)

    def read_com(self, event=None, text=None):  # функция обработки команд
        if text is None:  # если не передаётся параметр извне, то получаем команду из поля ввода
            text = self.command_entry.get()
            self.command_entry.delete(0, tk.END)  # очищаем поле ввода
        if not text:
            return
        self.text_out(self.username + "@" + self.hostname + "$ " + text)  # дублируем команду в поле вывода
        
        text = self.expand_vars(text)

        # парсер
        parts = text.split()
        if not parts:
            return
            
        comm = parts[0]
        arg = parts[1:] if len(parts) > 1 else []
        
        # обработка команд
        if comm == "ls":
            self.ls_com()
        elif comm == "cd":
            self.cd_com(arg)
        elif comm == "exit":
            self.exit_com()
        elif comm == "who":
            self.who_com()
        elif comm == "date":
            self.date_com()
        elif comm == "rm":
            self.rm_com(arg)
        elif comm == "pwd":
            self.pwd_com()
        else:
            self.text_out("command not found: " + comm)

    def exit_com(self):
        self.root.destroy()  # выход из программы

    def pwd_com(self):
        """Показать текущую директорию"""
        display_path = self.current_dir if self.current_dir else "/"
        self.text_out(display_path)

    def ls_com(self):
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        # Получаем файлы в текущей директории
        files_in_dir = []
        for f in self.vfs_files:
            if f.startswith(self.current_dir):
                # Получаем относительный путь
                relative = f[len(self.current_dir):]
                if relative:  # пропускаем саму директорию
                    first_part = relative.split('/')[0]
                    if first_part and first_part not in files_in_dir:
                        files_in_dir.append(first_part)
        
        if files_in_dir:
            self.text_out("\n".join(sorted(files_in_dir)))
        else:
            self.text_out("")  # пустой вывод для пустой директории

    def cd_com(self, args):
        if not args:
            self.text_out("cd: missing argument")
            return
            
        target_dir = args[0]
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return

        if target_dir == '/':  # переход в корень
            self.current_dir = ''
            self.virtual_env['PWD'] = '/'
            self.text_out("Changed directory to /")
            return
        elif target_dir == '..':  # переход на уровень выше
            if self.current_dir:
                parts = self.current_dir.rstrip('/').split('/')
                if parts:
                    parts.pop()
                    self.current_dir = '/'.join(parts)
                    if self.current_dir:
                        self.current_dir += '/'
                else:
                    self.current_dir = ''
            self.text_out(f"Changed directory to {self.current_dir or '/'}")
            self.virtual_env['PWD'] = self.current_dir if self.current_dir else '/'
            return
        
        # Проверяем существование целевой директории
        new_path = self.current_dir + target_dir
        if not new_path.endswith('/'):
            new_path += '/'
            
        # Проверяем, есть ли файлы в этой директории
        dir_exists = any(name.startswith(new_path) for name in self.vfs_files)
        if dir_exists:
            self.current_dir = new_path
            self.virtual_env['PWD'] = self.current_dir.rstrip('/') if self.current_dir else '/'
            self.text_out(f"Changed directory to {self.current_dir}")
        else:
            self.text_out(f"cd: {target_dir}: No such file or directory")

    def who_com(self):
        username = os.getlogin()  # получаем имя пользователя
        self.text_out(f"Username: {username}")

    def date_com(self):
        now = datetime.now()  # получаем дату и время
        # Форматируем в стиле Linux date: "Wed Sep 10 12:34:56 EEST 2025"
        formatted_date = now.strftime("%a %b %d %H:%M:%S %Z %Y")
        self.text_out(formatted_date)

    def rm_com(self, args):
        if not args:
            self.text_out("rm: missing operand")
            return
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        recursive = False
        targets = args
        
        # Обработка флага -r
        if args[0] == "-r":
            recursive = True
            targets = args[1:]
            
        if not targets:
            self.text_out("rm: missing operand")
            return
            
        for target in targets:
            target_path = self.current_dir + target
            if target_path.endswith('/'):
                target_path = target_path.rstrip('/')
                
            # Проверяем, является ли цель директорией
            is_dir = any(name.startswith(target_path + '/') and name != target_path for name in self.vfs_files)
            
            if is_dir and not recursive:
                self.text_out(f"rm: cannot remove '{target}': Is a directory")
                continue
                
            # Удаляем из списка файлов (в памяти)
            if is_dir:
                # Удаляем директорию и все её содержимое
                self.vfs_files = [name for name in self.vfs_files 
                                if not name.startswith(target_path + '/') and name != target_path]
                self.text_out(f"rm: removed directory '{target}' (in memory)")
            else:
                # Удаляем файл
                if target_path in self.vfs_files:
                    self.vfs_files.remove(target_path)
                    self.text_out(f"rm: removed file '{target}' (in memory)")
                else:
                    self.text_out(f"rm: cannot remove '{target}': No such file or directory")

    def start_script_run(self):
        with open(self.start_scr, 'r', encoding='utf-8') as f:  # открытие стартового скрипта
            for line_num, line in enumerate(f, 1):  # построчно читаем команды
                stripped = line.strip()
                if not stripped or stripped[0] == '#':  # если строка пустая или содержит комментарий, то переходим к следующей
                    continue
                try:
                    self.read_com(text=stripped)  # в обработчик команд отправляем прочитанную команду
                except Exception as e:
                    self.text_out(f"error in script: {self.start_scr} at line {line_num}: {str(e)}")
                    break

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--vfs")
    parser.add_argument("--script")  # для разделения аргументов командной строки

    args = parser.parse_args()
    
    root = tk.Tk()
    emulator = Emulator(root, vfs=args.vfs, start_scr=args.script)
    root.mainloop()