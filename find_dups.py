import os
from pprint import pprint
import hashlib
import sys
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style  

TO_DELETE_PATH=os.environ.get("TO_DELETE_PATH")
DRY_RUN="DRY_RUN" in os.environ

assert DRY_RUN or os.path.isdir(TO_DELETE_PATH)

def jm_walk(root):
    # complete list of files
    files = [
        os.path.join(path,file) 
        for path,dirs,files in os.walk(root) 
        for file in files
    ]
    # list of folders with at least one file
    dirs_with_files = set([os.path.dirname(f) for f in files])
    folders_content = {d: [] for d in dirs_with_files}
    # assign files to their folder
    for file in files:
        folders_content[os.path.dirname(file)].append(file)
    return folders_content

def get_file_tree(roots):
    file_tree = {}
    for root in roots:
        file_tree.update(jm_walk(root))
    return file_tree

def hash_func(file, hash_algo=hashlib.md5):
    with open(file, "rb") as f:
        file_hash = hash_algo()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def calculate_size_map(file_tree, del_duplicates=True):
    size_map = {}
    for path, files in file_tree.items():
        for file in files:
            size = os.path.getsize(file)
            if size in size_map:
                size_map[size].append(file)
            else:
                size_map[size] = [file]
    if del_duplicates:
        size_map = {k:v for k,v in size_map.items() if len(v) > 1}
    return size_map

def calculate_hash_map(file_tree=None, size_map=None, del_duplicates=True):
    hash_map = {}
    if not size_map:
        size_map = calculate_size_map(file_tree, del_duplicates=del_duplicates)
    for files in size_map.values():
        for file in files:
            hash = hash_func(file)
            if hash in hash_map:
                hash_map[hash].append(file)
            else:
                hash_map[hash] = [file]
    if del_duplicates:
        hash_map = {k: v for k,v in hash_map.items() if len(v) > 1}
    # unclear this is needed
    for v in hash_map.values():
        v.sort(key=os.path.basename)
    return hash_map
    
def calculate_folders_with_duplicates(hash_map):
    # find duplicates within the same directory first
    folders_with_duplicates = {}
    for duplicate_set in hash_map.values():
        base_dirs = tuple([os.path.dirname(f) for f in duplicate_set])
        if base_dirs in folders_with_duplicates:
            folders_with_duplicates[base_dirs].append(duplicate_set)
        else:
            folders_with_duplicates[base_dirs] = [duplicate_set]

    return folders_with_duplicates

def remove_bad_characters(roots,bad_chars=" ()"):
    for root in roots:
        for base_folder, _, files in os.walk(root):
            for file in files:
                base_path = base_folder + "/" + file
                new_path = base_path
                for c in bad_chars:
                    new_path = new_path.replace(c,"_")
                os.rename(base_path, new_path)

def get_choice(choice_set):
    assert not -1 in choice_set
    choice = -1
    while choice not in choice_set:
        choice = input("choice: ")
        for value in choice_set:
            try:
                formatted_choice = type(value)(choice)
                if formatted_choice == value:
                    return formatted_choice
            except ValueError as e:
                pass


def move_files_to_trash(to_move):
    print(f"{Fore.RED}DELETING {to_move}{Style.RESET_ALL}")
    confirm = input("confirm Y/N? ") == "Y"
    if not confirm:
        return
    
    for file in to_move:
        new_path = TO_DELETE_PATH + os.path.dirname(file)
        new_file = os.path.join(new_path, os.path.basename(file))
        os.makedirs(new_path, exist_ok=True)
        os.rename(file, new_file)

def file_date(f):
    return os.stat(f).st_ctime

def delete_duplicates_within_folders(roots):
    for root in roots:
        for path, files in jm_walk(root).items():
            hash_map = calculate_hash_map({path: files})
            if not hash_map:
                print(f"{Fore.BLUE}found NO duplicates in folder {path}{Style.RESET_ALL}")
            else:
                # try to sort them by date and keep the oldest
                files.sort(key=file_date)
                print(f"{Fore.YELLOW}found duplicates in folder {path}. suggesting the following actions:{Style.RESET_ALL}")
                for _, values in hash_map.items():
                    values_short = [os.path.basename(v) for v in values]
                    print(f"{Fore.GREEN}keep {values_short[0]}{Style.RESET_ALL} - ", end='')
                    print(f"{Fore.RED}DELETE {values_short[1:]}{Style.RESET_ALL}")
                if not DRY_RUN:
                    to_move = []
                    for values in hash_map.values():
                        to_move.extend(values[1:])
                    move_files_to_trash(to_move)

def delete_duplicate_folders(roots):
    file_tree = get_file_tree(roots)
    hash_map = calculate_hash_map(file_tree)
    folders_with_duplicates = calculate_folders_with_duplicates(hash_map)
    for folders, duplicates in folders_with_duplicates.items():
        num_duplicates = len(duplicates)
        folder_sizes = [len(file_tree[f]) for f in folders]
        if all([s == num_duplicates for s in folder_sizes]):
            print(f"{Fore.YELLOW}these folders contain the exact same files{Style.RESET_ALL}. What would you like to do?")
            print("[s]: Skip")
            for (i,to_keep) in enumerate(folders):
                to_delete = [f for f in folders if f != to_keep]
                print(f"[{i}]: {Fore.GREEN}keep {to_keep}{Style.RESET_ALL} {Fore.RED}(DELETE {to_delete}){Style.RESET_ALL}")
            if not DRY_RUN:
                choice = get_choice(['s'] + list(range(len(folders))))
                if choice == 's':
                    pass
                else: 
                    to_move = [
                        d
                        for dup_set in duplicates
                        for (i,d) in enumerate(dup_set)
                        if i != choice
                    ]
                    move_files_to_trash(to_move)

def delete_duplicate_files_between_folders(roots):
    file_tree = get_file_tree(roots)
    hash_map = calculate_hash_map(file_tree)
    folders_with_duplicates = calculate_folders_with_duplicates(hash_map)
    for folders, duplicates in folders_with_duplicates.items():
        print(f"{Fore.YELLOW}these folders contain duplicates: {folders}{Style.RESET_ALL}. What would you like to do?")
        print(f"{Fore.RED}{len(duplicates)} duplicates{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[s]: Skip{Style.RESET_ALL}")
        for (i,to_keep) in enumerate(folders):
            files_to_keep = [d[i].replace(to_keep,"")[1:] for d in duplicates]
            print(f"[{i}]: {Fore.GREEN}keep {to_keep} files: {files_to_keep}{Style.RESET_ALL} {Fore.RED}(DELETE THE OTHER OPTIONS){Style.RESET_ALL}")
        choice = get_choice(['s'] + list(range(len(folders))))
        if choice == 's':
            pass
        else: 
            to_move = [
                d
                for dup_set in duplicates
                for (i,d) in enumerate(dup_set)
                if i != choice
            ]
            move_files_to_trash(to_move)

def clean(roots):
    for root in roots:
        for path, dirs, files in os.walk(root, topdown=False):
            for d in dirs:
                dir = os.path.join(path, d)
                if not os.listdir(dir):
                    os.rmdir(dir)

if __name__ == "__main__":
    DUP_WITHIN = "DUP_WITHIN" in os.environ
    DUP_FOLDERS = "DUP_FOLDERS" in os.environ
    DUP_BETWEEN = "DUP_BETWEEN" in os.environ
    roots = sys.argv[1:]
    remove_bad_characters(roots, bad_chars=" ")
    if DUP_WITHIN:
        delete_duplicates_within_folders(roots)
    if DUP_FOLDERS:
        delete_duplicate_folders(roots)
    if DUP_BETWEEN:
        delete_duplicate_files_between_folders(roots)
    clean(roots)
