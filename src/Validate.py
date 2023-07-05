import pickle

from Models.BlockDAG.BlockDAGraph import BlockDAGraph
from ThesisStats import ThesisStats

INTERACTIVE = True



class Validate:
    last_order = []

    def validate(self, block_dag, ts):
        # Get ordering
        print("Timestamp: " + str(ts))
        ordering = block_dag.get_topological_ordering()
        ordering.reverse()

        print("Ordering: " + str(ordering))

        # Check if reorgs happened
        if len(ordering) > 1:
            if (Validate.detect_reorgs(self.last_order, ordering) != -1):
                print("Reorg detected at timestamp: " + str(ts))

        self.last_order = ordering

        # Calculate inclusion rate
        inclusion_matrix = ThesisStats.calculate_transaction_time_to_inclusion(block_dag)
        print("Inclusion matrix: ", inclusion_matrix)
        inclusion_rates = ThesisStats.calculate_inclusion_rates(inclusion_matrix)

        print("Inclusion rates: ", inclusion_rates)

    def detect_reorgs(first_order, second_order):
        # Find the first block that is different
        for i in range(0, len(first_order)):
            if first_order[i] != second_order[i]:
                # We found a reorg
                return i
        # No reorg found
        return -1

class Runner:
    def run():
        print("Running Validate.py")
        blockDAG: BlockDAGraph = pickle.load(open("node_99.pkl", "rb"))
        blockDAG.plot()

        # Get the timestamp of the last block
        max_ts = blockDAG.get_blockData_by_hash(blockDAG.get_last_block()).timestamp
        validator = Validate()

        print("Max timestamp: " + str(max_ts))
        for ts in range(0, int(max_ts), 100):

            # Exclude blocks before timestamp
            blockDAG_t = blockDAG.get_graph_before_timestamp(ts)
            validator.validate(blockDAG_t, ts)
            
            if INTERACTIVE:
                blockDAG_t.plot()
                input("Press Enter to continue...")

    # Run the run() function when this file is executed directly
    if __name__ == "__main__":
        run()

    
