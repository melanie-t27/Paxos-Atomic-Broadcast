


class Message:
    def __init__(self, id_source: int): 
        self.id_source = id_source


class Message1A(Message):
    def __init__(self, id_source: int, c_rnd : int):
        super().__init__(id_source)
        self.c_rnd = c_rnd


class Message1B(Message):
    def __init__(self, id_source: int, rnd: int, v_rnd: int, v_val: int):
        super().__init__(id_source)
        self.v_rnd = v_rnd
        self.rnd = rnd
        self.v_val = v_val


class Message2A(Message):
    def __init__(self, id_source: int, c_rnd: int, c_val: int):
        super().__init__(id_source)
        self.c_rnd = c_rnd
        self.c_val = c_val


class Message2B(Message):
    def __init__(self, id_source: int, v_rnd: int, v_val:int):
        super().__init__(id_source)
        self.v_rnd = v_rnd
        self.v_val = v_val


class DecisionMessage(Message):
    def __init__(self, id_source: int, v_val: int):
        super().__init__(id_source)
        self.v_val = v_val


class ClientMessage(Message):
    def __init__(self, id_source: int, value : int):
        super().__init__(id_source)
        self.value = value


    