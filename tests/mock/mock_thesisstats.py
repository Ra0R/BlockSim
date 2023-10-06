
from dataclasses import dataclass


class ThesisStats:
    def calculate_transaction_time_to_inclusion(block_dag):
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
            if descandant_blocks is None:
                continue


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
                        included_transactions = [transaction for transaction in transactions if transaction.id in included_transaction_ids]

                        if len(included_transactions) > 0:
                            # Calculate height difference
                            for transaction in included_transactions:
                                transaction_inclusion_matrix["transaction"].append(transaction.id)
                                transaction_inclusion_matrix["inclusion_time"].append(height_difference)
                                transaction_inclusion_matrix["reference_time"].append(-99)

                                # Initial fork id
                                transaction_inclusion_matrix["fork_id"].append(fork_id)
                                transaction_inclusion_matrix["included_in_block"].append(descendant_hash)
                                transaction_inclusion_matrix["included"].append(True)

                        elif descendant.references is not None and fork_id in descendant.references:
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
                                    if transaction_inclusion_matrix["inclusion_time"][index] > height_difference:
                                        transaction_inclusion_matrix["inclusion_time"][index] = height_difference
                                        transaction_inclusion_matrix["included"][index] = True
                                        transaction_inclusion_matrix["fork_id"][index] = fork_id
                                        transaction_inclusion_matrix["included_in_block"][index] = descendant_hash
                                        print(
                                            "Transaction with id: ", transaction.id,
                                            " is already included in the inclusion matrix but with a higher height difference")
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

    def calculate_inclusion_rates(inclusion_matrix, block_dag):
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
            inclusion_rate_later_time = 0
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
                            inclusion_rate_later_time += 1
                            time_to_reference_avg += inclusion_matrix["reference_time"][index]
                            time_to_reference_N += 1
                else:
                    print("Transaction with id: ", transaction.id,
                            " was not found in inclusion matrix (This shouldn't happen?)")

            if len(fork.transactions) == 0:
                print("Fork with id: ", fork_id, " has no transactions")
            else:
                conflict_inclusion_rate /= len(fork.transactions)
                inclusion_rate_later_time /= len(fork.transactions)
                avg_time_to_inclusion /= len(fork.transactions)
                if time_to_reference_N == 0:
                    time_to_reference_avg = -99
                else:
                    time_to_reference_avg /= time_to_reference_N

            inclusion_rates["fork_id"].append(fork_id)
            inclusion_rates["conflict_inclusion_rate"].append(conflict_inclusion_rate)
            inclusion_rates["reference_inclusion_rate"].append(inclusion_rate_later_time)
            inclusion_rates["time_to_inclusion_avg"].append(avg_time_to_inclusion)
            inclusion_rates["time_to_reference_avg"].append(time_to_reference_avg)

        return inclusion_rates
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
                "  transaction_count: " + str(self.transaction_count) + "\n"
    def predecessors_of_block(block_id, topological_order):
        """
        Returns the predecessors of a block in a topological order



        Args:
            block_id (_type_): _description_
            topological_order (_type_): Is sorted from lastest to earliest delivery: [-1, 0x1, 0x123,0x453]
        """
        index = topological_order.index(block_id)
        predecessors = topological_order[(index + 1):]
        print("Predecessors of block: ", block_id, " are: ", predecessors)

        return predecessors
        
    def calculate_transaction_troughput2(blockdag, main_chain, list_of_all_block_hashes, simTime):
        
        forked_blocks = set(list_of_all_block_hashes) - set(main_chain)
        # Need to order from earliest to latest
        # forked_blocks = sorted(forked_blocks, key=lambda x: x.timestamp)
        # for node in InputsConfig.NODES:
        fork_stats : list[ThesisStats.ForkStats] = []

        for forked_block in forked_blocks:
            conflict_inclusions = 0
            reference_inclusions = 0
            # Get all transactions
            block_data = blockdag.get_blockData_by_hash(forked_block)

            if block_data is None:
                print("ERROR -- Block with hash: ", forked_block, " does not exist on any node")
                continue
            earlier_transactions = []
            for predecessor in ThesisStats.predecessors_of_block(forked_block, list_of_all_block_hashes):
                predecessor_block_data = blockdag.get_blockData_by_hash(predecessor)
                if predecessor_block_data is None:
                    print("ERROR -- Block with hash: ", predecessor, " does not exist on any node")
                    continue
                earlier_transactions += predecessor_block_data.transactions

            for transaction in block_data.transactions:
                print("Transaction" + str(transaction.id) + " is in block " + str(forked_block) + " and was included in " + str(len(earlier_transactions)) + " earlier blocks")
                print("Earlier transactions: ", [x.id for x in earlier_transactions])
                if transaction.id in [tx.id for tx in earlier_transactions]:
                    conflict_inclusions += 1
                else:
                    reference_inclusions += 1

            fork_stats.append(ThesisStats.ForkStats(forked_block, conflict_inclusions, reference_inclusions, block_data.transactions, len(block_data.transactions)))
        for fork_stat in fork_stats:
            print(fork_stat)

        tx_delivered = 0
        # Calculate throughput
        for fork_stat in fork_stats:
            tx_delivered += fork_stat.reference_inclusions
                
        for mc_block in main_chain:
            block_data = blockdag.get_blockData_by_hash(mc_block)
            if block_data is None:
                print("ERROR -- Block with hash: ", mc_block, " does not exist on any node")
                continue
            tx_delivered += len(block_data.transactions)

        # Calculate throughput
        simulation_time = simTime
        transaction_count = tx_delivered
        throughput_sim = transaction_count / simulation_time
        real_time = simTime

        throughput_real = transaction_count / real_time

        return throughput_sim, throughput_real