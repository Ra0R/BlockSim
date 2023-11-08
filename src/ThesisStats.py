

import json
import math
from timeit import default_timer as timer
from dataclasses import dataclass

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from InputsConfig import InputsConfig
from Models.BlockDAG.BlockDAGraph import BlockDAGraph
from Models.BlockDAG.Consensus import Consensus
from RecordedBlock import MempoolOfNode
from ResultWriter import ResultWriter


class ThesisStats:

    START_T = 0
    END_T = 0
    WAITING_T = 0
    def jaccard_similarity(self, a, b):
        # calculate the Jaccard similarity coefficient
        set1 = set(a)
        set2 = set(b)
        try:
            jaccard_sim = len(set1.intersection(set2)) / len(set1.union(set2))
        except ZeroDivisionError:
            if len(set1) == 0 and len(set2) == 0:
                jaccard_sim = 1
            else:
                jaccard_sim = 0
        
        return jaccard_sim
    
    @dataclass
    class ForkStats:
        id: int
        conflict_inclusions: int
        reference_inclusions: int
        transactions: list
        transaction_count: int

        # toString without transactions
        def __str__(self):
            return "Fork: " + str(self.id) + "\n" + \
                "  conflict_inclusions: " + str(self.conflict_inclusions) + "\n" + \
                "  reference_inclusions: " + str(self.reference_inclusions) + "\n" + \
                "  transaction_count: " + str(self.transaction_count) + "\n" + \
                "  conflict_inclusion_rate:" + str(self.conflict_inclusions / self.transaction_count) + "\n" + \
                "  reference_inclusion_rate:" + str(self.reference_inclusions / self.transaction_count) + "\n"

    def mempool_similarity_matrix(self, mempoolsOfNode: list[MempoolOfNode]) -> list[list[float]]:
        # calculate the similarity matrix for the mempools
        similarity_matrix = []
        for i in range(len(mempoolsOfNode)):
            similarity_matrix.append([])
            for j in range(len(mempoolsOfNode)):
                mempool1 = mempoolsOfNode[i].mempool
                mempool2 = mempoolsOfNode[j].mempool

                # Convert mempool to list of hashes
                mempool1 = [tx.hash for tx in mempool1]
                mempool2 = [tx.hash for tx in mempool2]

                similarity_matrix[i].append(
                    self.jaccard_similarity(mempool1, mempool2))

        return similarity_matrix

    def plot_mempool_similarity_matrix(self, mempool_similarity_matrix: list[list[float]] = None, time=InputsConfig.simTime):
        import numpy as np

        sns.set_theme(style="white")

        mask = np.triu(np.ones_like(mempool_similarity_matrix, dtype=np.bool))

        # Add identity to the mask
        for i in range(len(mempool_similarity_matrix)):
            mask[i][i] = False

        f, ax = plt.subplots(figsize=(11, 9))

        cmap = sns.cubehelix_palette(as_cmap=True)
        # Add name of plot
        plt.title("Mempool similarity matrix at simulation time " + str(math.floor(time)) +"s of " + str(InputsConfig.simTime) + "s")

        sns.heatmap(mempool_similarity_matrix, mask=mask, cmap=cmap, vmin=0,
                    vmax=1, center=0.5,
                    square=True, linewidths=.5, cbar_kws={"shrink": .5}, annot=True,
                    xticklabels=[f"Node {i}" for i in range(
                        len(mempool_similarity_matrix))],
                    yticklabels=[f"Node {i}" for i in range(len(mempool_similarity_matrix))])

        # plt.draw()
        # plt.pause(0.01)

        return plt, f

    def calculate_fork_rate(list_of_all_block_hashes, main_chain_block_hashes):
        if len(list_of_all_block_hashes) == 0:
            return 0

        return (len(list_of_all_block_hashes) - len(main_chain_block_hashes)) / len(list_of_all_block_hashes)

    def calculate_stats(self, save_to_file=True, _blockDAG: BlockDAGraph = Consensus.get_global_blockDAG(), run=-1):
        if InputsConfig.model != 4:
            return
        # TODO: Remove k-prefix from the chains and check if they are consistent!

        blockDAGs = [node.blockDAG for node in InputsConfig.NODES]
        avg_fork_rate = ThesisStats.calculate_fork_rates_blockDAG(blockDAGs)
        
        list_of_all_block_hashes = _blockDAG.get_topological_ordering()
        main_chain = _blockDAG.get_main_chain()
        
        # TODO - rewrite these two
        # (!) Inclusion rates avg is wrong because it is not weighted by block
        inclusion_matrix = ThesisStats.calculate_transaction_time_to_inclusion()
        inclusion_rates = ThesisStats.calculate_inclusion_rates(inclusion_matrix)
        
        fork_stats = ThesisStats.calculate_fork_stats(main_chain, list_of_all_block_hashes)

        transaction_troughput_sim, transaction_troughput_real, throughput_real_optimal, throughput_real_bitcoin, throughput_sim_optimal, throughput_sim_bitcoin \
        = ThesisStats.calculate_transaction_troughput2(main_chain, fork_stats)
        for fork_stat in fork_stats:
            print(fork_stat)

        print("Avg fork rate: ", round(
            avg_fork_rate * 100, 2), "% [fork/blocks in DAG]")
        # print("Sim matrix: ", sim_matrix)
        print("Transaction troughput: (sim)", transaction_troughput_sim, "[tx/s]")
        print("Transaction troughput: (real)", transaction_troughput_real, "[tx/s]")
        print("Transaction troughput: (real optimal)", throughput_real_optimal, "[tx/s]")
        print("Transaction troughput: (real bitcoin)", throughput_real_bitcoin, "[tx/s]")
        # print("Time to inclusion: ", inclusion_matrix)
        # print("Inclusion rates: ", inclusion_rates)

        ThesisStats.save_output_to_disk(run, transaction_troughput_real, transaction_troughput_sim, throughput_real_optimal, throughput_sim_optimal, throughput_real_bitcoin, throughput_sim_bitcoin, inclusion_rates, avg_fork_rate, fork_stats)

    # def calculate_stats(self, save_to_file=True, blockDAG: BlockDAGraph = Consensus.get_global_blockDAG(), run=-1):
        # model = InputsConfig.model

        # if model == 1:
        #     avg_fork_rate = ThesisStats.calculate_fork_rates_blockChain()

        # if model == 4:
        #     blockDAGs = [node.blockDAG for node in InputsConfig.NODES]
        #     avg_fork_rate = ThesisStats.calculate_fork_rates_blockDAG(blockDAGs)
        #     if save_to_file:
        #         ThesisStats.save_nodes_to_disk()

        # sim_matrix = ThesisStats.calculate_mempool_similarity_matrix()

        # inclusion_matrix = ThesisStats.calculate_transaction_time_to_inclusion()
        # inclusion_rates = ThesisStats.calculate_inclusion_rates(inclusion_matrix)

        # transaction_troughput_sim, transaction_troughput_real = ThesisStats.calculate_transaction_troughput()
        # if InputsConfig.plot_inclusion:
        #     block_dag = Consensus.get_global_blockDAG()
        #     plot_data__inclusion_rate_per_block = ThesisStats.calculate_inclusion_rate_per_block(inclusion_matrix)
        #     block_dag.plot_with_inclusion_rate_per_block(plot_data__inclusion_rate_per_block)

        # # Save inclusion matrix to json file
        # with open('inclusion_matrix.json', 'w') as fp:
        #     json.dump(inclusion_matrix, fp)

        # print("Avg fork rate: ", round(
        #     avg_fork_rate * 100, 2), "% [fork/blocks in DAG]")
        # print("Sim matrix: ", sim_matrix)
        # print("Transaction troughput: (sim)", transaction_troughput_sim, "[tx/s]")
        # print("Transaction troughput: (real)", transaction_troughput_real, "[tx/s]")
        # # print("Time to inclusion: ", inclusion_matrix)
        # print("Inclusion rates: ", inclusion_rates)

        # Save stats to file
        #ThesisStats.save_output_to_disk(run, transaction_troughput_real, transaction_troughput_sim, inclusion_rates, avg_fork_rate)

    def save_output_to_disk(run, tps_real, tps_sim, optimal_tps_real, optimal_tps_sim, bitcoin_tps_real, bitcoin_tps_sim, inclusion_rates, fork_rate, fork_stats: list[ForkStats]):
        # Output has following format:
        # {
        #     params:
        #         {
        #         "const_node_count": 12
        #         "const_bsize": 1.0,
        #         "const_sim_time": 100 BLOCKS (?)

        #         "block_per_second": 123,
        #         "tx_delay": 123,
        #         "block_delay": 123132,
        #         "tx_per_second" : 10
        #         },
        #     results:
        #         {

        #             "tps": 123
        #             "inclusion_rate" :
        #             "inclusion_rate_per_fork" :
        #         }
        #     }

        if len(fork_stats) == 0:
            conflict_inclusion_rate_avg = 0
            reference_inclusion_rate_avg = 0
        else:
            conflict_inclusion_rate_avg = sum([i.conflict_inclusions for i in fork_stats]
                                              ) / sum([i.transaction_count for i in fork_stats])
            reference_inclusion_rate_avg = sum([i.reference_inclusions for i in fork_stats]
                                               ) / sum([i.transaction_count for i in fork_stats])

        # TODO: Fix this
        if len(inclusion_rates["time_to_reference_avg"]) == 0:
            reference_time_to_inclusion_avg = 0
        else:
            reference_time_to_inclusion_avg = sum([i for i in inclusion_rates["time_to_reference_avg"]
                                                   if i is not None]) / len([i
                                                                            for i in inclusion_rates["time_to_reference_avg"] if i is not None]),
        if len(inclusion_rates["time_to_inclusion_avg"]) == 0:
            conflict_time_to_inclusion_avg = 0
        else:
            conflict_time_to_inclusion_avg = sum(
                inclusion_rates["time_to_inclusion_avg"]) / len(inclusion_rates["time_to_inclusion_avg"]),

        output = {
            "params": {
                "const_node_count": len(InputsConfig.NODES),
                "const_bsize": InputsConfig.Bsize,
                "const_sim_time": InputsConfig.simTime,
                "block_creation_interval": InputsConfig.Binterval,
                "block_delay": InputsConfig.Bdelay,
                "tx_delay": InputsConfig.Tdelay,
                "tx_per_second": InputsConfig.Tn,
                "model": InputsConfig.model,
            },
            "results": {
                "optimal_tps_real": optimal_tps_real,
                "bitcoin_tps_real": bitcoin_tps_real,
                "tps_real": tps_real,
                "tps_sim": tps_sim,
                "optimal_tps_sim": optimal_tps_sim,
                "bitcoin_tps_sim": bitcoin_tps_sim,
                "conflict_inclusion_rate_all": inclusion_rates["conflict_inclusion_rate"],
                "conflict_time_to_inclusion_all": inclusion_rates["time_to_inclusion_avg"],
                "reference_inclusion_rate_all": inclusion_rates["reference_inclusion_rate"],
                "reference_time_to_inclusion_all": inclusion_rates["time_to_reference_avg"],
                "conflict_inclusion_rate_avg": conflict_inclusion_rate_avg,
                "conflict_time_to_inclusion_avg": conflict_time_to_inclusion_avg,
                "reference_inclusion_rate_avg": reference_inclusion_rate_avg,
                "reference_time_to_inclusion_avg": reference_time_to_inclusion_avg,
                "fork_rate": fork_rate,
                # "similarity_matrix": sim_matrix,
            }
        }

        # Save stats to file
        with open("output_param_" + str(run) + ".json", 'w') as fp:
            json.dump(output, fp)

    def save_nodes_to_disk():
        model = InputsConfig.model

        # if model == 1:
        #     for node in InputsConfig.NODES:
        #         node.save_to_disk()

        if model == 4:
            for node in InputsConfig.NODES:
                node.save_graph_to_file("node_" + str(node.id) + ".pkl")

    def calculate_fork_rates_blockChain():
        avg_fork_rate = 0
        for node in InputsConfig.NODES:
            main_chain = [block.id for block in Consensus.global_main_chain]
            list_of_all_block_hashes = [block.id for block in node.forkedBlocks]
            list_of_all_block_hashes += [block.id for block in node.blockchain]
            avg_fork_rate += ThesisStats.calculate_fork_rate(
                list_of_all_block_hashes, main_chain)

        avg_fork_rate /= len(InputsConfig.NODES)

        return avg_fork_rate

    def calculate_fork_rates_blockDAG(blockDAGs: list[BlockDAGraph]):
        avg_fork_rate = 0
        for blockDAG in blockDAGs:
            # list_of_all_block_hashes = blockDAG.to_list()
            list_of_all_block_hashes = blockDAG.get_topological_ordering()
            main_chain = blockDAG.get_main_chain()
            avg_fork_rate = ThesisStats.calculate_fork_rate(
                list_of_all_block_hashes, main_chain)
        avg_fork_rate /= len(blockDAGs)

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

    def calculate_inclusion_rates(inclusion_matrix, block_dag=Consensus.get_global_blockDAG()):
        inclusion_rates = {
            "fork_id": [],
            "conflict_inclusion_rate": [],
            "reference_inclusion_rate": [],
            "time_to_inclusion_avg": [],
            "time_to_reference_avg": [],
        }

        fork_ids = block_dag.get_forks()
        for fork_id in fork_ids:
            fork = block_dag.get_blockData_by_hash(fork_id)

            if fork is None:
                print("Trying to get Fork with id: ", fork_id,
                      " but it does not exist on any node")
                continue

            conflict_inclusion_rate = 0
            reference_inclusion_rate = 0
            avg_time_to_inclusion = 0
            time_to_reference_avg = 0
            time_to_reference_N = 0
            for transaction in fork.transactions:
                # Inclusion matrix is a dictionary with following structure:
                #  transaction_inclusion_matrix = {
                #       "transaction": [],
                #       "included": [],
                #       "inclusion_time": [],
                #       "fork_id": [],
                #       "included_in_block": []
                #   }

                if transaction.id in inclusion_matrix["transaction"]:
                    index = inclusion_matrix["transaction"].index(transaction.id)

                    if inclusion_matrix["included"][index] == True:
                        if inclusion_matrix["inclusion_time"][index] != -99:
                            conflict_inclusion_rate += 1
                            avg_time_to_inclusion += inclusion_matrix["inclusion_time"][index]
                        if inclusion_matrix["reference_time"][index] != -99:
                            reference_inclusion_rate += 1
                            time_to_reference_avg += inclusion_matrix["reference_time"][index]
                            time_to_reference_N += 1
                else:
                    print("Transaction with id: ", transaction.id,
                          " was not found in inclusion matrix (This shouldn't happen?)")

            if len(fork.transactions) == 0:
                print("Fork with id: ", fork_id, " has no transactions")
            else:
                conflict_inclusion_rate /= len(fork.transactions)
                reference_inclusion_rate /= len(fork.transactions)
                avg_time_to_inclusion /= len(fork.transactions)
                if time_to_reference_N == 0:
                    time_to_reference_avg = None
                else:
                    time_to_reference_avg /= time_to_reference_N

            inclusion_rates["fork_id"].append(fork_id)
            inclusion_rates["conflict_inclusion_rate"].append(conflict_inclusion_rate)
            inclusion_rates["reference_inclusion_rate"].append(reference_inclusion_rate)
            inclusion_rates["time_to_inclusion_avg"].append(avg_time_to_inclusion)
            inclusion_rates["time_to_reference_avg"].append(time_to_reference_avg)

        return inclusion_rates

    def calculate_mempool_similarity_matrix(plot=False, time=InputsConfig.simTime):

        sim_matrix = ThesisStats().mempool_similarity_matrix(
            ResultWriter.get_mempools(time))
        if InputsConfig.plot_similarity or plot:
            plt, f = ThesisStats().plot_mempool_similarity_matrix(sim_matrix, time)
            plt.show()

        return sim_matrix

    def predecessors_of_block(block_id, topological_order):
        """
        Returns the predecessors of a block in a topological order



        Args:
            block_id (_type_): _description_
            topological_order (_type_): Is sorted from lastest to earliest delivery: [-1, 0x1, 0x123,0x453]
        """
        index = topological_order.index(block_id)
        predecessors = topological_order[(index+1):]
        print("Predecessors of block: ", block_id, " are: ", predecessors)
        return predecessors


    def calculate_fork_stats(main_chain, list_of_all_block_hashes):
        forked_blocks = set(list_of_all_block_hashes) - set(main_chain)
        # for node in InputsConfig.NODES:
        fork_stats: list[ThesisStats.ForkStats] = []

        for forked_block in forked_blocks:
            conflict_inclusions = 0
            reference_inclusions = 0
            # Get all transactions
            block_data = Consensus.get_global_blockDAG().get_blockData_by_hash(forked_block)

            if block_data is None:
                print("ERROR -- Block with hash: ", forked_block, " does not exist on any node")
                continue
            earlier_transactions = []
            for predecessor in ThesisStats.predecessors_of_block(forked_block, list_of_all_block_hashes):
                predecessor_block_data = Consensus.get_global_blockDAG().get_blockData_by_hash(predecessor)
                if predecessor_block_data is None:
                    print("ERROR -- Block with hash: ", predecessor, " does not exist on any node")
                    continue
                earlier_transactions += predecessor_block_data.transactions

            earlier_ids = set([tx.id for tx in earlier_transactions])
            for transaction in block_data.transactions:
                # print("Transaction " + str(transaction.id) + " is in block " + str(forked_block) + " and was included in " + str(len(earlier_transactions)) + " earlier blocks")
                if transaction.id in earlier_ids:
                    conflict_inclusions += 1
                else:
                    reference_inclusions += 1

            fork_stats.append(
                ThesisStats.ForkStats(
                    forked_block, conflict_inclusions, reference_inclusions, block_data.transactions,len(block_data.transactions)))
            
        return fork_stats
        
    def calculate_transaction_troughput2(main_chain, fork_stats):
        tx_delivered = 0
        tx_delivered_optimal = 0
        tx_delivered_bitcoin = 0
        # Calculate throughput
        for fork_stat in fork_stats:
            tx_delivered += fork_stat.reference_inclusions
            tx_delivered_optimal += fork_stat.transaction_count
            tx_delivered_bitcoin += 0 # Bitcoin forked blocks are not included in the main chain
                
        for mc_block in main_chain:
            block_data = Consensus.get_global_blockDAG().get_blockData_by_hash(mc_block)
            if block_data is None:
                print("ERROR -- Block with hash: ", mc_block, " does not exist on any node")
                continue
            tx_delivered += len(block_data.transactions)
            tx_delivered_optimal += len(block_data.transactions)
            tx_delivered_bitcoin += len(block_data.transactions)

        # Calculate throughput
        simulation_time = InputsConfig.simTime
        transaction_count = tx_delivered

        throughput_sim = transaction_count / simulation_time
        real_time = ThesisStats.END_T - ThesisStats.START_T
        real_time += ThesisStats.WAITING_T

        throughput_real = transaction_count / real_time
        throughput_real_optimal = tx_delivered_optimal / real_time
        throughput_real_bitcoin = tx_delivered_bitcoin / real_time
        throughput_sim_optimal = tx_delivered_optimal / simulation_time
        throughput_sim_bitcoin = tx_delivered_bitcoin / simulation_time

        return throughput_sim, throughput_real, throughput_real_optimal, throughput_real_bitcoin, throughput_sim_optimal  , throughput_sim_bitcoin
            
    def calculate_transaction_troughput():
        simulation_time = InputsConfig.simTime
        transaction_count = 0
        if InputsConfig.model == 1:
            for node in InputsConfig.NODES:
                for block in node.blockchain:  # In this model it is the same as the main chain
                    transaction_count += len(block.transactions)
        elif InputsConfig.model == 4:
            for node in InputsConfig.NODES:
                # In this model all the blocks that are reachable from the last block are considered
                for block_id in node.blockDAG.get_reachable_blocks():
                    block_data = node.blockDAG.get_blockData_by_hash(block_id)
                    # This is wrong
                    if block_data is not None:
                        transaction_count += len(block_data.transactions)

        throughput = transaction_count / len(InputsConfig.NODES)
        real_time = ThesisStats.END_T - ThesisStats.START_T
        real_time += ThesisStats.WAITING_T
        # real_time = real_time / len(InputsConfig.NODES)
        
        print("Real time: ", real_time, " seconds")
        print("Simulation time: ", simulation_time, " seconds")
        throughput_sim = throughput / simulation_time
        throughput_real = throughput / real_time
        
        return throughput_sim, throughput_real

    def calculate_transaction_time_to_inclusion(block_dag: BlockDAGraph = Consensus.get_global_blockDAG()):
        """
        If anybody wants to use this function, please read the following:
        Don't do it
        """

        if InputsConfig.model == 1:
            True
        if InputsConfig.model == 4:
          # node = InputsConfig.NODES[0]
            # block_dag = node.blockDAG

            # forks = block_dag.get_reachable_blocks() - set(block_dag.get_main_chain())
            forks = block_dag.get_forks()

            transaction_inclusion_matrix = {
                "transaction": [],
                "included": [],
                "inclusion_time": [],
                "reference_time": [],
                "fork_id": [],
                "included_in_block": []
            }

            main_chain = block_dag.get_main_chain()

            for fork_id in forks:
                fork = block_dag.get_blockData_by_hash(fork_id)

                if fork is None:
                    # Sometimes fork is not on any node, so we skip it
                    continue

                previous_block = block_dag.get_blockData_by_hash(fork_id).previous
                descandant_blocks = block_dag.get_descendants(previous_block)

                descandant_blocks.discard(previous_block)
                descandant_blocks.discard(fork_id)

                transactions = block_dag.get_blockData_by_hash(fork_id).transactions

                for descendant_hash in descandant_blocks:
                    descendant = block_dag.get_blockData_by_hash(descendant_hash)

                    if descendant is not None:
                        height_difference = descendant.depth - fork.depth
                        if height_difference < 0:
                            print("Height difference is negative")
                        else:
                            # Check if the transactions are included in the descendant
                            set1 = set([transaction.id for transaction in transactions])
                            set2 = set([transaction.id for transaction in descendant.transactions])
                            included_transaction_ids = set1.intersection(set2)
                            included_transactions = [
                                transaction for transaction in transactions
                                if transaction.id in included_transaction_ids]

                            if len(included_transactions) > 0:
                                # Calculate height difference
                                for transaction in included_transactions:

                                    # Check if the transaction is included in the Block
                                    if transaction.id not in transaction_inclusion_matrix["transaction"]:
                                        transaction_inclusion_matrix["transaction"].append(transaction.id)
                                        transaction_inclusion_matrix["inclusion_time"].append(height_difference)
                                        transaction_inclusion_matrix["reference_time"].append(-99)

                                        # Initial fork id
                                        transaction_inclusion_matrix["fork_id"].append(fork_id)
                                        transaction_inclusion_matrix["included_in_block"].append(descendant_hash)
                                        transaction_inclusion_matrix["included"].append(True)
                                    else:
                                        index = transaction_inclusion_matrix["transaction"].index(transaction.id)
                                        if transaction_inclusion_matrix["inclusion_time"][index] > height_difference or transaction_inclusion_matrix["reference_time"][index] > height_difference:
                                            print("Updating tx (refrence)" + str(transaction.id) +
                                                  " with height difference " + str(height_difference) + " and fork id " +
                                                  str(fork_id) + " and included in block " + str(descendant_hash))
                                            transaction_inclusion_matrix["reference_time"][index] = -99
                                            transaction_inclusion_matrix["inclusion_time"][index] = height_difference
                                            transaction_inclusion_matrix["included"][index] = True
                                            transaction_inclusion_matrix["fork_id"][index] = fork_id
                                            transaction_inclusion_matrix["included_in_block"][index] = descendant_hash

                            # Otherwise check if the descendant references the fork
                            if descendant.references is not None and descendant_hash in main_chain and fork_id in descendant.references:
                                # If the descendant references the fork, then the transaction is included
                                for transaction in transactions:
                                    # Chekc if the transaction is already included
                                    if transaction.id not in transaction_inclusion_matrix["transaction"]:
                                        transaction_inclusion_matrix["transaction"].append(transaction.id)

                                        transaction_inclusion_matrix["inclusion_time"].append(-99)
                                        transaction_inclusion_matrix["reference_time"].append(height_difference)

                                        transaction_inclusion_matrix["included"].append(True)
                                        transaction_inclusion_matrix["fork_id"].append(fork_id)
                                        transaction_inclusion_matrix["included_in_block"].append(descendant_hash)
                                    else:
                                        # Check if the transaction is included in a block with a lower height difference
                                        index = transaction_inclusion_matrix["transaction"].index(transaction.id)
                                        if transaction_inclusion_matrix["inclusion_time"][index] > height_difference or transaction_inclusion_matrix["reference_time"][index] > height_difference:
                                            print("Updating tx (refrence)" + str(transaction.id) +
                                                  " with height difference " + str(height_difference) + " and fork id " +
                                                  str(fork_id) + " and included in block " + str(descendant_hash))
                                            transaction_inclusion_matrix["reference_time"][index] = height_difference
                                            transaction_inclusion_matrix["inclusion_time"][index] = -99
                                            transaction_inclusion_matrix["included"][index] = True
                                            transaction_inclusion_matrix["fork_id"][index] = fork_id
                                            transaction_inclusion_matrix["included_in_block"][index] = descendant_hash

                                            # This happens when the block has been checked before

                # All transactions that are not included in the descendants are not included
                for transaction in transactions:
                    if transaction.id not in transaction_inclusion_matrix["transaction"]:
                        transaction_inclusion_matrix["transaction"].append(transaction.id)
                        transaction_inclusion_matrix["inclusion_time"].append(-99)
                        transaction_inclusion_matrix["reference_time"].append(-99)
                        transaction_inclusion_matrix["included"].append(False)
                        transaction_inclusion_matrix["fork_id"].append(-1)
                        transaction_inclusion_matrix["included_in_block"].append(-1)

        return transaction_inclusion_matrix
