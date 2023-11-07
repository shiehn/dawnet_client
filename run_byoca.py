import byoac


def arbitrary_method(a: int, b: str):
    print(f"Received an int: {a} and a string: {b}")


byoac.connect_to_server(token='dc308761-9aeb-4667-bb71-f11d87fec665')
byoac.register_method("arbitrary_method", arbitrary_method)