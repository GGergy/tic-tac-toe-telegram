import json


class CallbackDataClass:
    def __init__(self, handler, **kwargs):
        self.handler = handler
        for key, item in kwargs.items():
            self.__setattr__(key, item)

    def __getattr__(self, item):
        return self.__dict__.get(item, None)

    def __repr__(self):
        return "Callback data: " + ", ".join([f"{key} - {item}" for key, item in self.__dict__.items()])


def call_in(js_line: str) -> CallbackDataClass:
    data = json.loads(js_line)
    handler = data.pop('handler')
    return CallbackDataClass(handler=handler, **data)


def lambda_generator(handler):
    return lambda call: call_in(call.data).handler == handler


def call_out(handler: str, **kwargs) -> str:
    kwargs['handler'] = handler
    return json.dumps(kwargs)
