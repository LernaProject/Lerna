import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_logging(cnf):
    import logging.config

    if 'handlers' in cnf:
        for handler in cnf['handlers'].values():
            if 'filename' in handler:
                os.makedirs(os.path.dirname(handler['filename']), exist_ok=True)

    logging.logThreads = logging.logProcesses = False
    return logging.config.dictConfig(cnf)


def _init_settings():
    import yaml

    def adjust_path(loader, node): return os.path.join(BASE_DIR, loader.construct_scalar(node))
    yaml.add_constructor('!path', adjust_path)

    configuration_files = ('settings.yml', 'local_settings.yml', 'static_files_settings.yml')
    for filename in configuration_files:
        with open(os.path.join(BASE_DIR, 'lerna', filename)) as f:
            for key, value in yaml.load(f).items():
                if key == 'PREPEND':
                    for key, value in value.items():
                        globals()[key] = value + globals()[key]
                elif key == 'APPEND':
                    for key, value in value.items():
                        globals()[key] += value
                elif key == 'OVERRIDE':
                    for cnf, sub in value.items():
                        cnf = globals()[cnf]
                        for key, value in sub.items():
                            cnf[key] = value
                else:
                    globals()[key] = value


_init_settings()
