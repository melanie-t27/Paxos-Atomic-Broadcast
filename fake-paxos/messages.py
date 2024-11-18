class Message:
    def __init__(self, id_instance: int, id_source: int): 
        self.id_instance = id_instance
        self.id_source = id_source


class Message1A(Message):
    def __init__(self, id_instance: int, id_source: int, c_rnd : int):
        super().__init__(id_instance, id_source)
        self.c_rnd = c_rnd


class Message1B(Message):
    def __init__(self, id_instance: int, id_source: int, rnd: int, v_rnd: int, v_val: list[int]):
        super().__init__(id_instance, id_source)
        self.v_rnd = v_rnd
        self.rnd = rnd
        self.v_val = v_val


class Message2A(Message):
    def __init__(self, id_instance: int, id_source: int, c_rnd: int, c_val: list[int]):
        super().__init__(id_instance, id_source)
        self.c_rnd = c_rnd
        self.c_val = c_val


class Message2B(Message):
    def __init__(self, id_instance: int, id_source: int, v_rnd: int, v_val: list[int]):
        super().__init__(id_instance, id_source)
        self.v_rnd = v_rnd
        self.v_val = v_val


class DecisionMessage(Message):
    def __init__(self, id_instance: int, id_source: int, v_val: list[int]):
        super().__init__(id_instance, id_source)
        self.v_val = v_val


class ClientMessage(Message):
    def __init__(self, id_source: int, value : list[int]):
        super().__init__(-1, id_source)
        self.values = value