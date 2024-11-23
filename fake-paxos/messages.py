class Message:
    def __init__(self, id_instance: int): 
        self.id_instance = id_instance


class Message1A(Message):
    def __init__(self, id_instance: int, c_rnd : int):
        super().__init__(id_instance)
        self.c_rnd = c_rnd


class Message1B(Message):
    def __init__(self, id_instance: int, rnd: int, v_rnd: int, v_val: list[int], id_source: int):
        super().__init__(id_instance)
        self.v_rnd = v_rnd
        self.rnd = rnd
        self.v_val = v_val
        self.id_source = id_source


class Message2A(Message):
    def __init__(self, id_instance: int, c_rnd: int, c_val: list[int], id_source: int):
        super().__init__(id_instance)
        self.c_rnd = c_rnd
        self.c_val = c_val
        self.id_source = id_source


class Message2B(Message):
    def __init__(self, id_instance: int, v_rnd: int, v_val: list[int], id_source: int):
        super().__init__(id_instance)
        self.v_rnd = v_rnd
        self.v_val = v_val
        self.id_source = id_source


class DecisionMessage(Message):
    def __init__(self, id_instance: int, v_val: list[int]):
        super().__init__(id_instance)
        self.v_val = v_val


class ClientMessage(Message):
    def __init__(self, id_source: int, value : list[int]):
        super().__init__(-1)
        self.id_source = id_source
        self.values = value

class LearnerArrivalMessage(Message):
    def __init__(self):
        super().__init__(-1)

class NotifyClientMessage(Message):
    def __init__(self, id_source: int):
        super().__init__(-1)
        self.id_source = id_source