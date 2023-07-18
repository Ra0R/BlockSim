
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
