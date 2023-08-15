

import json
from timeit import default_timer as timer

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from InputsConfig import InputsConfig
from Models.BlockDAG.BlockDAGraph import BlockDAGraph
from Models.BlockDAG.Consensus import Consensus
from RecordedBlock import MempoolOfNode
from ResultWriter import ResultWriter


class ThesisStats:

    def jaccard_similarity(self, a, b):
        # calculate the Jaccard similarity coefficient
        set1 = set(a)
        set2 = set(b)
        jaccard_sim = len(set1.intersection(set2)) / len(set1.union(set2))
        return jaccard_sim

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

    def plot_mempool_similarity_matrix(self, mempool_similarity_matrix: list[list[float]] = None):
        import numpy as np

        sns.set_theme(style="white")

        mask = np.triu(np.ones_like(mempool_similarity_matrix, dtype=np.bool))

        # Add identity to the mask
        for i in range(len(mempool_similarity_matrix)):
            mask[i][i] = False

        f, ax = plt.subplots(figsize=(11, 9))

        cmap = sns.diverging_palette(230, 20, as_cmap=True)
        # Add name of plot
        plt.title("Mempool similarity matrix")

        sns.heatmap(mempool_similarity_matrix, mask=mask, cmap=cmap, vmin=0,
                    vmax=1, center=0.5,
                    square=True, linewidths=.5, cbar_kws={"shrink": .5}, annot=True,
                    xticklabels=[f"Node {i}" for i in range(
                        len(mempool_similarity_matrix))],
                    yticklabels=[f"Node {i}" for i in range(len(mempool_similarity_matrix))])

        # plt.draw()
        # plt.pause(0.01)

        return plt

    def calculate_fork_rate(list_of_all_block_hashes, main_chain_block_hashes):
        if len(list_of_all_block_hashes) == 0:
            return 0

        return (len(list_of_all_block_hashes) - len(main_chain_block_hashes)) / len(list_of_all_block_hashes)

    def calculate_stats(self, save_to_file=True, blockDAG: BlockDAGraph = Consensus.get_global_blockDAG(), run=-1):
        model = InputsConfig.model

        if model == 1:
            avg_fork_rate = ThesisStats.calculate_fork_rates_blockChain()

        if model == 4:
            blockDAGs = [node.blockDAG for node in InputsConfig.NODES]
            avg_fork_rate = ThesisStats.calculate_fork_rates_blockDAG(blockDAGs)
            if save_to_file:
                ThesisStats.save_nodes_to_disk()

        sim_matrix = ThesisStats.calculate_mempool_similarity_matrix()

        transaction_troughput_sim, transaction_troughput_real = ThesisStats.calculate_transaction_troughput()

        inclusion_matrix = ThesisStats.calculate_transaction_time_to_inclusion()
        inclusion_rates = ThesisStats.calculate_inclusion_rates(inclusion_matrix)

        if InputsConfig.plot_inclusion:
            block_dag = Consensus.get_global_blockDAG()
            plot_data__inclusion_rate_per_block = ThesisStats.calculate_inclusion_rate_per_block(inclusion_matrix)
            block_dag.plot_with_inclusion_rate_per_block(plot_data__inclusion_rate_per_block)

        # Save inclusion matrix to json file
        with open('inclusion_matrix.json', 'w') as fp:
            json.dump(inclusion_matrix, fp)

        print("Avg fork rate: ", round(
            avg_fork_rate * 100, 2), "% [fork/blocks in DAG]")
        print("Sim matrix: ", sim_matrix)
        print("Transaction troughput: (sim)", transaction_troughput_sim, "[tx/s]")
        print("Transaction troughput: (real)", transaction_troughput_real, "[tx/s]")
        # print("Time to inclusion: ", inclusion_matrix)
        print("Inclusion rates: ", inclusion_rates)

        # Save stats to file
        ThesisStats.save_output_to_disk(run, transaction_troughput_real, transaction_troughput_sim, inclusion_rates, avg_fork_rate)

    def save_output_to_disk(run, tps_real, tps_sim, inclusion_rates, fork_rate):
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
                "tps_real": tps_real,
                "tps_sim": tps_sim,
                "conflict_inclusion_rate_all": inclusion_rates["conflict_inclusion_rate"],
                "conflict_time_to_inclusion_all": inclusion_rates["time_to_inclusion_avg"],
                "reference_inclusion_rate_all": inclusion_rates["reference_inclusion_rate"],
                "reference_time_to_inclusion_all": inclusion_rates["time_to_reference_avg"],
                "conflict_inclusion_rate_avg": sum(inclusion_rates["conflict_inclusion_rate"]) / len(inclusion_rates["conflict_inclusion_rate"]),
                "conflict_time_to_inclusion_avg": sum(inclusion_rates["time_to_inclusion_avg"]) / len(inclusion_rates["time_to_inclusion_avg"]),
                "reference_inclusion_rate_avg": sum(inclusion_rates["reference_inclusion_rate"]) / len(inclusion_rates["reference_inclusion_rate"]),
                "reference_time_to_inclusion_avg": sum([i for i in inclusion_rates["time_to_reference_avg"] if i is not None]) / len([i for i in inclusion_rates["time_to_reference_avg"] if i is not None]),
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
            list_of_all_block_hashes = [
                block.id for block in node.forkedBlocks]
            list_of_all_block_hashes += [block.id for block in node.blockchain]
            avg_fork_rate += ThesisStats.calculate_fork_rate(
                list_of_all_block_hashes, main_chain)

        avg_fork_rate /= len(InputsConfig.NODES)

        return avg_fork_rate

    def calculate_fork_rates_blockDAG(blockDAGs: list[BlockDAGraph]):
        avg_fork_rate = 0
        for blockDAG in blockDAGs:
            list_of_all_block_hashes = blockDAG.to_list()
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
            plt = ThesisStats().plot_mempool_similarity_matrix(sim_matrix)
            plt.show(block=True)

        return sim_matrix

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
                    if block_data is not None:
                        transaction_count += len(block_data.transactions)

        throughput = transaction_count / len(InputsConfig.NODES)

        throughput_sim = throughput / simulation_time
        throughput_real = throughput / timer()
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
