import pickle

from Models.BlockDAG.BlockDAGraph import BlockDAGraph
from ThesisStats import ThesisStats

INTERACTIVE = True


def detect_reorgs(first_order, second_order):
    # Find the first block that is different
    for i in range(0, len(first_order)):
        if first_order[i] != second_order[i]:
            # We found a reorg
            return i
    # No reorg found
    return -1


class Validate:

    def run():
        print("Running Validate.py")
        blockDAG: BlockDAGraph = pickle.load(open("node_99.pkl", "rb"))
        blockDAG.plot()

        # Get the timestamp of the last block
        max_ts = blockDAG.get_blockData_by_hash(blockDAG.get_last_block()).timestamp
        last_order = []
        print("Max timestamp: " + str(max_ts))
        for ts in range(0, int(max_ts), 100):

            # Exclude blocks before timestamp
            blockDAG_t = blockDAG.get_graph_before_timestamp(ts)
            print("Timestamp: " + str(ts))
            ordering = blockDAG_t.get_topological_ordering()
            ordering.reverse()

            print("Ordering: " + str(ordering))

            # Check if reorgs happened
            if len(ordering) > 1:
                if (detect_reorgs(last_order, ordering) != -1):
                    print("Reorg detected at timestamp: " + str(ts))

            last_order = ordering

            if INTERACTIVE:
                blockDAG_t.plot()
                input("Press Enter to continue...")

            ThesisStats.calculate_stats(False, blockDAG_t, ts)

    # Run the run() function when this file is executed directly
    if __name__ == "__main__":
        run()
