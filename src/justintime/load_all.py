import os.path
import importlib
import logging

pages = []
plots = []
ctrls = []
run_new = True

def loader(path, *args, ignore = []):

    objects = []

    registry_module = importlib.import_module(f".{path}.registry", "justintime")
    components = registry_module.component_list
    for comp in components:
        logging.debug(f"Loading {comp}.py module from .{path}.content")
        module = importlib.import_module(f".{path}.content.{comp}", "justintime")
        objects.append(module.return_obj(*args))

    return(objects)
    # file_list = os.listdir(f"{os.path.dirname(__file__)}/{path}/content")

    # for file in file_list:
    #     root, ext = os.path.splitext(file)
    #     if file not in ignore and not file.startswith('__') and (ext == ".py"):
    #         logging.debug(f"Loading {file} module from .{path}.content")
    #         module = importlib.import_module(f".{path}.content.{root}", "justintime")
    #         objects.append(module.return_obj(*args))
    # objects.sort(key=lambda obj: obj.id)
    # return(objects)

def get_elements(dash_app = [], engine = [], storage = [], theme=[]):
    global pages, plots, ctrls, run_new
    if run_new:
        pages = loader("pages")
        plots = loader("plots", dash_app, engine, storage, theme)
        ctrls = loader("controls", dash_app, engine, storage)

        run_new = False
    return(pages, plots, ctrls)








