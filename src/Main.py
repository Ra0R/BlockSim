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
            BlockCommit.handle_event(next_event)
            event_log.append(next_event)
            Queue.remove_event(next_event)
            # InputsConfig.NODES[0].blockDAG.plot()
            # plt = ThesisStats().plot_mempool_similarity_matrix(ThesisStats().mempool_similarity_matrix(ResultWriter.get_mempools()))

        if InputsConfig.plot_similarity:
            plt = ThesisStats().plot_mempool_similarity_matrix(
                ThesisStats().mempool_similarity_matrix(ResultWriter.get_mempools()))
            plt.show()

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
            for node in InputsConfig.NODES[0:3]:
                node.blockDAG.plot()
                input("Press Enter to continue...")

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
        Statistics.reset()
        
        ResultWriter.writeResult()
        ResultWriter.writeEvents(event_log, with_transactions=False)
        

######################################################## Run Main method #####################################################################
if __name__ == '__main__':
    main()
