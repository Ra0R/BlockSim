import json

from Event import Event, Queue
from InputsConfig import InputsConfig as InputsConfig
from ResultWriter import ResultWriter
from Scheduler import Scheduler
from Statistics import Statistics
from ThesisStats import ThesisStats


def profile(f): return f

if InputsConfig.model == 3:
    from Models.AppendableBlock.BlockCommit import BlockCommit
    from Models.AppendableBlock.Node import Node
    from Models.AppendableBlock.Statistics import Statistics
    from Models.AppendableBlock.Transaction import FullTransaction as FT
    from Models.AppendableBlock.Verification import Verification
    from Models.Consensus import Consensus
    from Models.Incentives import Incentives

elif InputsConfig.model == 2:
    from Models.Ethereum.BlockCommit import BlockCommit
    from Models.Ethereum.Consensus import Consensus
    from Models.Ethereum.Incentives import Incentives
    from Models.Ethereum.Node import Node
    from Models.Ethereum.Transaction import FullTransaction as FT
    from Models.Ethereum.Transaction import LightTransaction as LT

elif InputsConfig.model == 1:
    from Models.Bitcoin.BlockCommit import BlockCommit
    from Models.Bitcoin.Consensus import Consensus
    from Models.Bitcoin.Node import Node
    from Models.Incentives import Incentives
    from Models.Transaction import FullTransaction as FT
    from Models.Transaction import LightTransaction as LT

elif InputsConfig.model == 0:
    from Models.BlockCommit import BlockCommit
    from Models.Consensus import Consensus
    from Models.Incentives import Incentives
    from Models.Node import Node
    from Models.Transaction import FullTransaction as FT
    from Models.Transaction import LightTransaction as LT

elif InputsConfig.model == 4:
    from Models.BlockCommit import BlockCommit
    from Models.BlockDAG.BlockCommit import BlockCommit
    from Models.BlockDAG.Consensus import Consensus
    from Models.BlockDAG.Node import Node
    from Models.Transaction import FullTransaction as FT
    

########################################################## Start Simulation ##############################################################

@profile
def main():
    event_log = []
    for i in range(InputsConfig.Runs):
        clock = 0  # set clock to 0 at the start of the simulation
        if InputsConfig.hasTrans:
            if InputsConfig.Ttechnique == "Light":
                LT.create_transactions()  # generate pending transactions
            elif InputsConfig.Ttechnique == "Full":
                FT.create_transactions()  # generate pending transactions

        Node.generate_gensis_block()  # generate the gensis block for all miners
        # initiate initial events >= 1 to start with
        BlockCommit.generate_initial_events()
        while not Queue.isEmpty() and clock <= InputsConfig.simTime:
            next_event = Queue.get_next_event()
            clock = next_event.time  # move clock to the time of the event
        
            if InputsConfig.plot_similarity_progress and len(event_log) % 45 == 0:
                calculate_mempool_similarity_matrix(True, clock)
           
            BlockCommit.handle_event(next_event)
            event_log.append(next_event)
            Queue.remove_event(next_event)

        # for the AppendableBlock process transactions and
        # optionally verify the model implementation
        if InputsConfig.model == 3:
            BlockCommit.process_gateway_transaction_pools()

            if i == 0 and InputsConfig.VerifyImplemetation:
                Verification.perform_checks()

        Consensus.fork_resolution()  # apply the longest chain to resolve the forks
        # distribute the rewards between the particiapting nodes
        if not InputsConfig.model == 4:
            Incentives.distribute_rewards()
        
        # calculate the simulation results (e.g., block statstics and miners' rewards)
        if not InputsConfig.model == 4:
            Statistics.calculate()

        if InputsConfig.model == 4:
            if InputsConfig.plot_chain:
                for node in InputsConfig.NODES[0:3]:
                    node.blockDAG.plot()
                    input("Press Enter to continue...")
        """
        # if InputsConfig.model == 3:
        #     Statistics.print_to_excel(i, True)
        #     Statistics.reset()
        # else:
        #     ########## reset all global variable before the next run #############
        #     Statistics.reset()  # reset all variables used to calculate the results
        #     Node.resetState()  # reset all the states (blockchains) for all nodes in the network
        #     fname = "(Allverify)1day_{0}M_{1}K.xlsx".format(
        #         InputsConfig.Bsize/1000000, InputsConfig.Tn/1000)
        #     # print all the simulation results in an excel file
        #     Statistics.print_to_excel(fname)
        # fname = "(Allverify)1day_{0}M_{1}K.xlsx".format(
        #         InputsConfig.Bsize/1000000, InputsConfig.Tn/1000)
        # # print all the simulation results in an excel file
        # Statistics.print_to_excel(fname)
        # Statistics.reset2()  # reset profit results

        # Node.reset_state()
        """
        # ResultWriter.writeResult()
        # ResultWriter.writeEvents(event_log, with_transactions=False)

        calculate_stats()

        Statistics.reset()
        

def calculate_stats():
    avg_fork_rate = calculate_fork_rate()
    sim_matrix = calculate_mempool_similarity_matrix()
    transaction_troughput = calculate_transaction_troughput()
    inclusion_matrix = calculate_transaction_time_to_inclusion()

    inclusion_rates = calculate_inclusion_rates(inclusion_matrix)

    inclusion_rate_per_block = calculate_inclusion_rate_per_block(inclusion_matrix)
    block_dag = Consensus.get_global_blockDAG()
    if InputsConfig.plot_inclusion:
        block_dag.plot_with_inclusion_rate_per_block(inclusion_rate_per_block)

    # Save inclusion matrix to json file
    with open('inclusion_matrix.json', 'w') as fp:
        json.dump(inclusion_matrix, fp)

    print("Avg fork rate: ", round(avg_fork_rate * 100,2), "% [fork/blocks in DAG]")
    print("Sim matrix: ", sim_matrix)
    print("Transaction troughput: ", transaction_troughput, "[tx/s]")
    # print("Time to inclusion: ", inclusion_matrix)
    print("Inclusion rates: ", inclusion_rates)

def calculate_fork_rate():
    model = InputsConfig.model

    avg_fork_rate = 0
    if model == 1:
        for node in InputsConfig.NODES:
            main_chain = [block.id for block in Consensus.global_main_chain]
            list_of_all_block_hashes = [block.id for block in node.forkedBlocks]
            list_of_all_block_hashes += [block.id for block in node.blockchain]
            avg_fork_rate  += ThesisStats().calculate_fork_rate(list_of_all_block_hashes, main_chain)

    if model == 4:
        # Avg over all nodes
        for node in InputsConfig.NODES:
            list_of_all_block_hashes = node.blockDAG.to_list()
            main_chain = node.blockDAG.get_main_chain()
            avg_fork_rate += ThesisStats().calculate_fork_rate(list_of_all_block_hashes, main_chain)
        

    avg_fork_rate /= len(InputsConfig.NODES)

    return avg_fork_rate

def calculate_inclusion_rate_per_block(inclusion_matrix):
    inclusion_rate_per_block = {
        "fork_id": [],
        "block_id": [],
        "inclusion_rate": [],
        "inclusion_time": [],
    }

    block_dag = Consensus.get_global_blockDAG()

    for i in range(len(inclusion_matrix["fork_id"])):
        fork_id = inclusion_matrix["fork_id"][i]
        block_id = inclusion_matrix["included_in_block"][i]
        included = inclusion_matrix["included"][i]
        inclusion_time = inclusion_matrix["inclusion_time"][i]

        if included == True:
            if fork_id not in inclusion_rate_per_block["fork_id"]:
                inclusion_rate_per_block["fork_id"].append(fork_id)
                inclusion_rate_per_block["block_id"].append(block_id)
                inclusion_rate_per_block["inclusion_rate"].append(1)
                inclusion_rate_per_block["inclusion_time"].append(inclusion_time)
            else:
                index = inclusion_rate_per_block["fork_id"].index(fork_id)
                inclusion_rate_per_block["inclusion_rate"][index] += 1
    
    for i in range(len(inclusion_rate_per_block["fork_id"])):
        fork_id = inclusion_rate_per_block["fork_id"][i]
        fork = block_dag.get_blockData_by_hash(fork_id)
        inclusion_rate_per_block["inclusion_rate"][i] /= len(fork.transactions)
    print("Inclusion rate per block: ", inclusion_rate_per_block)
    return inclusion_rate_per_block


def calculate_inclusion_rates(inclusion_matrix):
    inclusion_rates = {
        "fork_id": [],
        "inclusion_rate": [],
        "inclusion_rate_later_time" : [],
        "inclusion_rate_by_reference": []
   }

    block_dag = Consensus.get_global_blockDAG()

    fork_ids = get_forks(block_dag)
    for fork_id in fork_ids:
            fork = block_dag.get_blockData_by_hash(fork_id)
            
            if fork is None:
                print("Trying to get Fork with id: ", fork_id, " but it does not exist on any node")
                continue

            fork_inclusion_rate = 0
            inclusion_rate_later_time = 0
            for transaction in fork.transactions:
                # Inclusion matrix is a dictionary with following structure:
                #         transaction_inclusion_matrix = {
                #   "transaction": [],
                #   "included": [],
                #   "inclusion_time": [],
                #   "fork_id": [],
                #    "included_in_block": []
                #}
                if transaction.id in inclusion_matrix["transaction"]:
                    index = inclusion_matrix["transaction"].index(transaction.id)
                    if inclusion_matrix["included"][index] == True:
                        fork_inclusion_rate += 1 
                    # TODO - This is wrong -> This only means that a later block tried to include the transaction
                    # but it does not mean that it was included in the block
                    if inclusion_matrix["inclusion_time"][index] > 0:
                        inclusion_rate_later_time += 1
            if len(fork.transactions) == 0:
                print("Fork with id: ", fork_id, " has no transactions")
            else:
                fork_inclusion_rate /= len(fork.transactions)
                inclusion_rate_later_time /= len(fork.transactions)

            inclusion_rates["fork_id"].append(fork_id)
            inclusion_rates["inclusion_rate"].append(fork_inclusion_rate)
            # inclusion_rates["inclusion_rate_later_time"].append(inclusion_rate_later_time)
    
    return inclusion_rates

def calculate_mempool_similarity_matrix(plot=False, time=InputsConfig.simTime):
    
    sim_matrix = ThesisStats().mempool_similarity_matrix(ResultWriter.get_mempools(time))
    if InputsConfig.plot_similarity or plot:
        plt = ThesisStats().plot_mempool_similarity_matrix(sim_matrix)
        plt.show(block=True)

    return sim_matrix

def calculate_transaction_troughput():
    simulation_time = InputsConfig.simTime
    troughput = 0
    if InputsConfig.model == 1:
        for node in InputsConfig.NODES:
            for block in node.blockchain: # In this model it is the same as the main chain
                troughput += len(block.transactions)
    elif InputsConfig.model == 4:
        for node in InputsConfig.NODES:
            for block_id in node.blockDAG.get_reachable_blocks(): # In this model all the blocks that are reachable from the last block are considered
                block_data = node.blockDAG.get_blockData_by_hash(block_id)
                if block_data is not None:
                    troughput += len(block_data.transactions)

    troughput /= len(InputsConfig.NODES)
    troughput /= simulation_time

    return troughput

def get_forks(blockDAG):
    forks = blockDAG.get_reachable_blocks() - set(blockDAG.get_main_chain())
    return forks

def calculate_transaction_time_to_inclusion():
    # Inclusion horizon
    inclusion_horizon = 50

    if InputsConfig.model == 1:
        True
    if InputsConfig.model == 4:
        # node = InputsConfig.NODES[0]
        # block_dag = node.blockDAG
        block_dag = Consensus.get_global_blockDAG()
        
        forks = block_dag.get_reachable_blocks() - set(block_dag.get_main_chain())
        transaction_inclusion_matrix = {
            "transaction": [],
            "included": [],
            "inclusion_time": [],
            "fork_id": [],
            "included_in_block": []
        }

        for fork_id in forks:
            fork = block_dag.get_blockData_by_hash(fork_id)
            
            if fork is None:
                # Sometimes fork is not on any node, so we skip it
                continue
            previous = block_dag.get_blockData_by_hash(fork_id).previous
            descendants = block_dag.get_descendants(previous) 

            descendants.discard(previous)
            descendants.discard(fork_id)

            transactions = block_dag.get_blockData_by_hash(fork_id).transactions
            if descendants is None:
                continue

            for descendant_hash in descendants:
                descendant = block_dag.get_blockData_by_hash(descendant_hash)
                if descendant is not None:
                    height_difference = descendant.depth - fork.depth
                    if  height_difference < 0:
                        print("Height difference is negative")
                    if height_difference < inclusion_horizon:
                        # Check if the transactions are included in the descendant
                        set1 = set([transaction.id for transaction in transactions])
                        set2 = set([transaction.id for transaction in descendant.transactions])
                        included_transaction_ids = set1.intersection(set2)
                        included_transactions = [transaction for transaction in transactions if transaction.id in included_transaction_ids]
                        
                        if len(included_transactions) > 0:
                            # Calculate height difference
                            for transaction in included_transactions:
                                transaction_inclusion_matrix["transaction"].append(transaction.id)
                                transaction_inclusion_matrix["inclusion_time"].append(height_difference)
                                # Initial fork id
                                transaction_inclusion_matrix["fork_id"].append(fork_id)
                                transaction_inclusion_matrix["included_in_block"].append(descendant_hash)
                                transaction_inclusion_matrix["included"].append(True)

            # All transactions that are not included in the descendants are not included
            for transaction in transactions:
                if transaction.id not in transaction_inclusion_matrix["transaction"]:
                    transaction_inclusion_matrix["transaction"].append(transaction.id)
                    transaction_inclusion_matrix["inclusion_time"].append(-99)
                    transaction_inclusion_matrix["included"].append(False)
                    transaction_inclusion_matrix["fork_id"].append(-1)
                    transaction_inclusion_matrix["included_in_block"].append(-1)


    return transaction_inclusion_matrix         



######################################################## Run Main method #####################################################################
if __name__ == '__main__':
    main()
