import os
import logging
import importlib

def submodules_loader(path, modlist, *args, ignore = []):
    objects = []
    file_list = os.listdir(path)
    for file in file_list:
        root, ext = os.path.splitext(file)
        if file not in ignore and not file.startswith('__') and (ext == ".py"):
            logging.debug(f"Loading {file} module from .{path}.content")
            module = importlib.import_module(f".{path}.content.{root}", "justintime")
            objects.append(module.return_obj(*args))
    objects.sort(key=lambda obj: obj.id)
    return(objects)