from InputsConfig import InputsConfig
from Models.Block import Block as BaseBlock


class Block(BaseBlock):

    def __init__(self,
                 depth=0,
                 id=0,
                 timestamp=0,
                 rx_timestamp=[0 for _ in range(InputsConfig.Nn)],
                 miner=None,
                 transactions=[],
                 size=1.0,
                 previous=-1,
                 references=[],
                 ):

        super().__init__(depth, id, previous, timestamp, miner, transactions, size)
        self.references = references
        self.rx_timestamp = rx_timestamp

    def __str__(self) -> str:
        return super().__str__() + " references: " + str(self.references)