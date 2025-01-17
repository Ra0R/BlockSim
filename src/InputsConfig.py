
class InputsConfig:
    RESULTS_PATH = "Results/"
    """ Seclect the model to be simulated.
    0 : The base model
    1 : Bitcoin model
    2 : Ethereum model
    3 : AppendableBlock model
    4 : BlockDAG model
    """
    seed = 42
    seed_creation = True
    model = 4
    plot_similarity = False
    plot_chain = True
    print_progress = True
    plot_inclusion = False
    confirmation_depth = 6 # Number of blocks to wait for confirmation
    ''' Input configurations for the base model '''
    if model == 0:

        ''' Block Parameters '''
        Binterval = 600  # Average time (in seconds)for creating a block in the blockchain
        Bsize = 1.0  # The block size in MB
        Bdelay = 0.42  # average block propogation delay in seconds, #Ref: https://bitslog.wordpress.com/2016/04/28/uncle-mining-an-ethereum-consensus-protocol-flaw/
        Breward = 12.5  # Reward for mining a block

        ''' Transaction Parameters '''
        hasTrans = True  # True/False to enable/disable transactions in the simulator
        Ttechnique = "Light"  # Full/Light to specify the way of modelling transactions
        Tn = 10  # The rate of the number of transactions to be created per second
        # The average transaction propagation delay in seconds (Only if Full technique is used)
        Tdelay = 5.1
        Tfee = 0.000062  # The average transaction fee
        Tsize = 0.000546  # The average transaction size  in MB

        ''' Node Parameters '''
        Nn = 3  # the total number of nodes in the network
        NODES = []
        from Models.Node import Node

        # here as an example we define three nodes by assigning a unique id for each one
        NODES = [Node(id=0), Node(id=1)]

        ''' Simulation Parameters '''
        simTime = 1000  # the simulation length (in seconds)
        Runs = 1  # Number of simulation runs

    ''' Input configurations for Bitcoin model '''
    ''' Input configurations for the BlockDAG model'''
    if model == 1 or model == 4:
        ''' Block Parameters '''
        Binterval = 10  # Average time (in seconds)for creating a block in the blockchain
        Bsize = 1.0  # The block size in MB
        Bdelay = 10 # average block propogation delay in seconds #https://bitcoin.stackexchange.com/questions/10821/how-long-does-it-take-to-propagate-a-newly-created-block-to-the-entire-bitcoin-n

        Breward = 12.5  # Reward for mining a block

        ''' Transaction Parameters '''
        hasTrans = True  # True/False to enable/disable transactions in the simulator
        Ttechnique = "Full"  # Full/Light to specify the way of modelling transactions
        Tn = 60  # The rate of the number of transactions to be created per second
        
        tx_consistency = True # If disabled, transactions may be included twice

        # The average transaction propagation delay in seconds (Only if Full technique is used)
        Tdelay = 15.1
        Tfee = 0.000062  # The average transaction fee
        Tsize = 0.000546  # The average transaction size  in MB

        ''' Node Parameters '''
        Nn = 4  # the total number of nodes in the network
        NODES = []
        if model == 1:
            from Models.Bitcoin.Node import Node
        else:
            from Models.BlockDAG.Node import Node

        # NODES = [Node(id=i, hashPower=100) for i in range(0, 100)]
        # here as an example we define three nodes by assigning a unique id for each one + % of hash (computing) power
        NODES = [
            Node(id=0, hashPower=25), 
            Node(id=1, hashPower=25), 
            Node(id=2, hashPower=25),
            Node(id=3, hashPower=25),
            # Node(id=4, hashPower=20),
            # Node(id=5, hashPower=10),
            # Node(id=6, hashPower=10),
            # Node(id=7, hashPower=10),
            # Node(id=8, hashPower=10),
            # Node(id=9, hashPower=10),
            # Node(id=10, hashPower=10),
            # Node(id=11, hashPower=10),
            # Node(id=12, hashPower=10),
        ]


        ''' Simulation Parameters '''
        simTime = 100  # the simulation length (in seconds)
        Runs = 1  # Number of simulation runs
        
    ''' Input configurations for Ethereum model '''
    if model == 2:

        ''' Block Parameters '''
        Binterval = 12.42  # Average time (in seconds)for creating a block in the blockchain
        Bsize = 1.0  # The block size in MB
        Blimit = 8000000  # The block gas limit
        Bdelay = 6  # average block propogation delay in seconds, #Ref: https://bitslog.wordpress.com/2016/04/28/uncle-mining-an-ethereum-consensus-protocol-flaw/
        Breward = 2  # Reward for mining a block

        ''' Transaction Parameters '''
        hasTrans = True  # True/False to enable/disable transactions in the simulator
        Ttechnique = "Light"  # Full/Light to specify the way of modelling transactions
        Tn = 20  # The rate of the number of transactions to be created per second
        # The average transaction propagation delay in seconds (Only if Full technique is used)
        Tdelay = 3
        # The transaction fee in Ethereum is calculated as: UsedGas X GasPrice
        Tsize = 0.000546  # The average transaction size  in MB

        ''' Drawing the values for gas related attributes (UsedGas and GasPrice, CPUTime) from fitted distributions '''

        ''' Uncles Parameters '''
        hasUncles = True  # boolean variable to indicate use of uncle mechansim or not
        Buncles = 2  # maximum number of uncle blocks allowed per block
        Ugenerations = 7  # the depth in which an uncle can be included in a block
        Ureward = 0
        UIreward = Breward / 32  # Reward for including an uncle

        ''' Node Parameters '''
        Nn = 3  # the total number of nodes in the network
        NODES = []
        from Models.Ethereum.Node import Node

        # here as an example we define three nodes by assigning a unique id for each one + % of hash (computing) power
        NODES = [
                Node(id=0, hashPower=50),
                Node(id=1, hashPower=20),
                Node(id=2, hashPower=30)
                ]

        ''' Simulation Parameters '''
        simTime = 500  # the simulation length (in seconds)
        Runs = 2  # Number of simulation runs

        ''' Input configurations for AppendableBlock model '''
    if model == 3:
        ''' Transaction Parameters '''
        Bsize = 1.0 # The block size in MB
        hasTrans = True  # True/False to enable/disable transactions in the simulator

        Ttechnique = "Full"

        # The rate of the number of transactions to be created per second
        Tn = 10

        # The maximum number of transactions that can be added into a transaction list
        txListSize = 100

        ''' Node Parameters '''
        # Number of device nodes per gateway in the network
        Dn = 10
        # Number of gateway nodes in the network
        Gn = 2
        # Total number of nodes in the network
        Nn = Gn + (Gn*Dn)
        # A list of all the nodes in the network
        NODES = []
        # A list of all the gateway Ids
        GATEWAYIDS = [chr(x+97) for x in range(Gn)]
        from Models.AppendableBlock.Node import Node

        # Create all the gateways
        for i in GATEWAYIDS:
            otherGatewayIds = GATEWAYIDS.copy()
            otherGatewayIds.remove(i)
            # Create gateway node
            NODES.append(Node(i, "g", otherGatewayIds))

        # Create the device nodes for each gateway
        deviceNodeId = 1
        for i in GATEWAYIDS:
            for j in range(Dn):
                NODES.append(Node(deviceNodeId, "d", i))
                deviceNodeId += 1

        ''' Simulation Parameters '''
        # The average transaction propagation delay in seconds
        propTxDelay = 0.000690847927

        # The average transaction list propagation delay in seconds
        propTxListDelay = 0.00864894

        # The average transaction insertion delay in seconds
        insertTxDelay = 0.000010367235

        # The simulation length (in seconds)
        simTime = 500

        # Number of simulation runs
        Runs = 5

        ''' Verification '''
        # Varify the model implementation at the end of first run
        VerifyImplemetation = True

        maxTxListSize = 0
