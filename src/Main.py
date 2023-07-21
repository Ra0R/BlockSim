import json
import math
import sys
from timeit import default_timer as timer

from Event import Event, Queue
from InputsConfig import InputsConfig as InputsConfig
from ParameterSpace import ParameterSpace
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
    start_t = timer()
    event_log = []
    arg_len = len(sys.argv)
    if arg_len > 1:
        # Initialize simulation parameter space
        params = ParameterSpace()
        # Get the combination of parameters to be used in this simulation
        print("Running simulation combination id " + str(sys.argv[1]) + "/" + str(len(params.combinations)) + " (" + str(params.combinations[int(sys.argv[1])]) + ")")
        combination = params.get_combination(int(sys.argv[1]))
        
        InputsConfig.Binterval = combination[0]
        InputsConfig.Tdelay = combination[1]
        InputsConfig.Bdelay = combination[2]
        # InputsConfig.Tn = combination[3] # TODO Set this to a multiple of block size
        InputsConfig.simTime = InputsConfig.Binterval * 100 # Generate a hundred blocks

        # We want to generate more transactions than those that fit in a block
        InputsConfig.Tn = math.ceil((InputsConfig.Bsize / InputsConfig.Tsize) * InputsConfig.Binterval)
        
        print("------------------------------------")
        print("Running simulation with parameters:")
        print("Binterval: " + str(InputsConfig.Binterval))
        print("Tdelay: " + str(InputsConfig.Tdelay))
        print("Bdelay: " + str(InputsConfig.Bdelay))
        print("Tn: " + str(InputsConfig.Tn))
        print("------------------------------------")


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
            ThesisStats.calculate_mempool_similarity_matrix(True, clock)
        
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
            for node in InputsConfig.NODES:
                print("Main chain contains NO DUPLICATES:" + str(node.blockDAG.post_check_transaction_validity_main_chain()))

                if InputsConfig.plot_chain:
                    node.blockDAG.plot(node.id)
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
    ResultWriter.writeResult()
    # ResultWriter.writeEvents(event_log, with_transactions=False)

    ThesisStats().calculate_stats(run=sys.argv[1] if arg_len > 1 else -1)

    Statistics.reset()
        

     



######################################################## Run Main method #####################################################################
if __name__ == '__main__':
    main()
