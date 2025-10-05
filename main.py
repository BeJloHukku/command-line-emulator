import tkinter as tk
from tkinter import *
import os
from datetime import datetime
import platform
import xml.etree.ElementTree as ET
from pathlib import Path
import re

def get_names():
    username = os.getlogin()
    hostname = platform.node()
    return username, hostname

class Emulator:
    def __init__(self, root, vfs=None, start_scr=None):
        self.root = root
        self.start_time = datetime.now()
        if vfs:
            self.vfs = vfs
        else:
            self.vfs = os.path.expanduser("~\Desktop\KFG\command-line-emulator-work\\vfs_data\.my_vfs\\vfs1.xml")
        self.start_scr = start_scr
        self.current_dir = ''
        self.virtual_env = {
            'HOME': '/',
            'PWD': '/',
        }
        print("Параметры эмулятора")
        print("VFS - " + self.vfs)
        print("Start Script - " + (self.start_scr if self.start_scr else "None"))
        
        self.username, self.hostname = get_names()
        self.root.title("Эмулятор - " + self.username + "@" + self.hostname)
        
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.command_entry = tk.Entry(self.input_frame, width=80)
        self.command_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.command_entry.bind("<Return>", self.read_com)
        
        self.prompt_label = tk.Label(self.input_frame, text="Введите команду", width=20)
        self.prompt_label.pack()
        
        self.but_frame = tk.Frame(root)
        self.but_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.enter_but = tk.Button(self.but_frame, text="Выполнить команду", width=20, pady=5, command=self.read_com)  # кнопка для ввода команды
        self.enter_but.pack(side=tk.LEFT, fill=tk.BOTH)
        
        self.output_frame = tk.Frame(root)
        self.output_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.output_text = tk.Text(self.output_frame)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        self.start_vfs()
        if self.start_scr and os.path.exists(self.start_scr):
            self.start_script_run()
        elif self.start_scr:
            self.text_out(f"error: startup script not found: {self.start_scr}")

    def expand_vars(self, text):
        """Заменяет $VAR и ${VAR} на значения из VFS"""
        def replace(match):
            var_name = match.group(1) or match.group(2)
            return self.virtual_env.get(var_name, '')
        
        return re.sub(r'\$(\w+)|\$\{(\w+)\}', replace, text)
    

    def start_vfs(self):
        try:
            if not os.path.exists(self.vfs):
                self.text_out(f"VFS NOT FOUND: {self.vfs}")
                self.vfs_tree = None
                self.vfs_files = []
                return
                
            self.vfs_tree = ET.parse(self.vfs)
            self.vfs_root = self.vfs_tree.getroot()
            
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
        for child in element:
            if child.tag == 'directory':
                dir_name = child.get('name', '')
                dir_path = current_path + dir_name + '/'
                self.vfs_files.append(dir_path)
                self._collect_files(child, dir_path)
            elif child.tag == 'file':
                file_name = child.get('name', '')
                file_path = current_path + file_name
                self.vfs_files.append(file_path)

    def _find_element(self, path):
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
        self.output_text.insert(tk.END, s + "\n")
        self.output_text.see(tk.END)

    def read_com(self, event=None, text=None):
        if text is None:
            text = self.command_entry.get()
            self.command_entry.delete(0, tk.END)
        if not text:
            return
        self.text_out(self.username + "@" + self.hostname + "$ " + text)  
        
        text = self.expand_vars(text)

        parts = text.split()
        if not parts:
            return
            
        comm = parts[0]
        arg = parts[1:] if len(parts) > 1 else []
        
        if comm == "ls":
            self.ls_com()
        elif comm == "cd":
            self.cd_com(arg)
        elif comm == "exit":
            self.exit_com()
        elif comm == "vfs-save":
            self.vfs_save_com(arg)
        elif comm == "uptime":
            self.uptime_com()
        elif comm == "tail":
            self.tail_com(arg)
        elif comm == "touch":
            self.touch_com(arg)
        elif comm == "head":
            self.head_com(arg)
        elif comm == "chown":
            self.chown_com(arg)
        else:
            self.text_out("command not found: " + comm)

    def exit_com(self):
        self.root.destroy()

    def pwd_com(self):
        """Показать текущую директорию"""
        display_path = self.current_dir if self.current_dir else "/"
        self.text_out(display_path)

    def ls_com(self):
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        files_in_dir = []
        for f in self.vfs_files:
            if f.startswith(self.current_dir):
                relative = f[len(self.current_dir):]
                if relative:
                    first_part = relative.split('/')[0]
                    if first_part and first_part not in files_in_dir:
                        files_in_dir.append(first_part)
        
        if files_in_dir:
            self.text_out("\n".join(sorted(files_in_dir)))
        else:
            self.text_out("")

    def cd_com(self, args):
        if not args:
            self.text_out("cd: missing argument")
            return
            
        target_dir = args[0]
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return

        if target_dir == '/':
            self.current_dir = ''
            self.virtual_env['PWD'] = '/'
            self.text_out("Changed directory to /")
            return
        elif target_dir == '..':
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
        
        new_path = self.current_dir + target_dir
        if not new_path.endswith('/'):
            new_path += '/'

        dir_exists = any(name.startswith(new_path) for name in self.vfs_files)
        if dir_exists:
            self.current_dir = new_path
            self.virtual_env['PWD'] = self.current_dir.rstrip('/') if self.current_dir else '/'
            self.text_out(f"Changed directory to {self.current_dir}")
        else:
            self.text_out(f"cd: {target_dir}: No such file or directory")


    def vfs_save_com(self, args):
        if not args:
            self.text_out("vfs-save: missing file path")
            return
            
        save_path = args[0]
        
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        try:
            new_vfs = ET.Element('vfs')
            
            dirs = set()
            files = set()
            
            for path in self.vfs_files:
                if path.endswith('/'):
                    dirs.add(path.rstrip('/'))
                else:
                    files.add(path)
            
            dir_tree = {}
            for dir_path in dirs:
                parts = dir_path.split('/')
                current = dir_tree
                for part in parts:
                    if part:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
            
            for file_path in files:
                parts = file_path.split('/')
                dir_parts = parts[:-1]
                filename = parts[-1]
                
                current = dir_tree
                for part in dir_parts:
                    if part:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                
                current[filename] = None
            
            self.build_xml(new_vfs, dir_tree)
            
            tree = ET.ElementTree(new_vfs)
            tree.write(save_path, encoding='utf-8', xml_declaration=True)
            
            self.text_out(f"VFS saved to: {save_path}")
            
        except Exception as e:
            self.text_out(f"vfs-save error: {e}")

    def build_xml(self, parent, tree):
        for name, children in sorted(tree.items()):
            if children is None:
                ET.SubElement(parent, 'file', name=name)
            else:
                dir_elem = ET.SubElement(parent, 'directory', name=name)
                self.build_xml(dir_elem, children)
    def uptime_com(self):
        current_time = datetime.now()
        uptime = current_time - self.start_time
        total_seconds = int(uptime.total_seconds())
        days = total_seconds // (24 * 3600)
        hours = (total_seconds % (24 * 3600)) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            uptime_str = f"{days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        self.text_out(f"up {uptime_str}")
        self.text_out(f"started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def start_script_run(self):
        with open(self.start_scr, 'r', encoding='utf-8') as f:  
            for line_num, line in enumerate(f, 1):  
                stripped = line.strip()
                if not stripped or stripped[0] == '#': 
                    continue
                try:
                    self.read_com(text=stripped)  
                except Exception as e:
                    self.text_out(f"error in script: {self.start_scr} at line {line_num}: {str(e)}")
                    break

    def head_com(self, args):
        """Показывает первые 10 строк файла"""
        if not args:
            self.text_out("head: missing file operand")
            return
            
        filename = args[0]
        lines = 10
        
        file_path = self.current_dir + filename
        
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        file_element = self._find_element(file_path)
        
        if file_element is None or file_element.tag != 'file':
            self.text_out(f"head: {filename}: No such file")
            return
            
        content = self.get_file_content(file_element, file_path)
        
        content_lines = content.split('\n')
        for i in range(min(lines, len(content_lines))):
            self.text_out(content_lines[i])
    
    def tail_com(self, args):
        if not args:
            self.text_out("tail: missing file operand")
            return
            
        filename = args[0]
        lines = 10
        
        file_path = self.current_dir + filename
        
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        file_element = self._find_element(file_path)
        
        if file_element is None or file_element.tag != 'file':
            self.text_out(f"tail: {filename}: No such file")
            return
            
        content = self.get_file_content(file_element, file_path)
        
        content_lines = content.split('\n')
        start_index = max(0, len(content_lines) - lines)
        
        for i in range(start_index, len(content_lines)):
            self.text_out(content_lines[i])
    
    def get_file_content(self, file_element, file_path):
        content = file_element.get('content', '')
        if not content:
            content = "Nothing"
        content = content.replace('\\n', '\n').replace('\\t', '\t')
        return content
    
    def chown_com(self, args):
        if len(args) < 2:
            self.text_out("chown: missing operand")
            self.text_out("Usage: chown OWNER FILE...")
            return
            
        new_owner = args[0]
        targets = args[1:]
        
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        success_count = 0
        for target in targets:
            target_path = self.current_dir + target
            
            if target_path in self.vfs_files or any(name.startswith(target_path + '/') for name in self.vfs_files):
                self.text_out(f"chown: changing ownership of '{target}' to '{new_owner}' (in memory)")
                success_count += 1
            else:
                self.text_out(f"chown: cannot access '{target}': No such file or directory")
        
        if success_count > 0:
            self.text_out(f"chown: changed ownership of {success_count} item(s)")

    def touch_com(self, args):
        if not args:
            self.text_out("touch: missing file operand")
            return
            
        if not self.vfs_tree:
            self.text_out("VFS NOT FOUND")
            return
            
        success_count = 0
        for filename in args:
            file_path = self.current_dir + filename
            
            if file_path in self.vfs_files:
                self.text_out(f"touch: updated timestamp of '{filename}' (in memory)")
                success_count += 1
            else:
                self.vfs_files.append(file_path)
                self.text_out(f"touch: created file '{filename}' (in memory)")
                success_count += 1

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--vfs")
    parser.add_argument("--script")  # для разделения аргументов командной строки

    args = parser.parse_args()
    
    root = tk.Tk()
    emulator = Emulator(root, vfs=args.vfs, start_scr=args.script)
    root.mainloop()