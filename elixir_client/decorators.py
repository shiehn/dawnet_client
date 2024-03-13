# decorators.py
def ui_param(name, ui_component, **kwargs):
    def decorator(func):
        if not hasattr(func, "_ui_params"):
            func._ui_params = {}
        func._ui_params[name] = {"ui_component": ui_component, **kwargs}
        return func

    return decorator
