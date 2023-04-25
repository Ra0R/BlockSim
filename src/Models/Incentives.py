from InputsConfig import InputsConfig as InputsConfig
from Models.Consensus import Consensus as Consensus


class Incentives:

    """
	 Defines the rewarded elements (block + transactions), calculate and distribute the rewards among the participating nodes
    """
    def distribute_rewards():
        for bc in Consensus.global_main_chain:
            for m in InputsConfig.NODES:
                if bc.miner == m.id:
                    m.blocks +=1
                    m.balance += InputsConfig.Breward # increase the miner balance by the block reward
                    tx_fee= Incentives.transactions_fee(bc)
                    m.balance += tx_fee # add transaction fees to balance


    def transactions_fee(bc):
        fee=0
        for tx in  bc.transactions:
            fee += tx.fee
        return fee
