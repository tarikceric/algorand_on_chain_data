# Algorand On-Chain Data - Overview

This repository is focused on accessing on-chain data from the Algorand blockchain as directly as possible and retrieving some insights from the data. To accomplish this without the use of a 3rd party api, an extensive amount of research was done on how to properly set up a node in the Algorand blockchain to get access to the full set of available data on the chain.

To fully interact with the chain, a node must be installed and ran. A quick method to set this up is to utilize the Algorand Sandbox, which uses a Docker container to set up a node. Also, to access a node independently of external providers, the Algorand Indexer must be installed separetely to read the blockchain data. The challenge with this is the sheer size as the indexer needs to 'catch up' with the Algorand blockchain from its genesis. 

In order to provide practical functionality, the scripts are set up to be able to access data through the REST API provided by a self-managed node, as well as allowing connections to 3rd party APIs (ie Algoexplorer/Purestake) -- it would simply require inserting the correct API key and Algorand node address in the ```config.py``` file.
* To use a 3rd party API such as Algoexplorer or Purestake, use 'https://algoindexer.algoexplorerapi.io' / "https://mainnet-algorand.api.purestake.io/idx2" for the REST API url,  and the token can be left blank.
  * Note: PureStake's API, when used with the Algorand SDK, requires an alternate header value 'X-API-Key', which can be added in the config file
* When using a self-managed node, use the local host utilized by  the indexer ( ie. "http://localhost:8980") and the token that is provided following the install.

The data exploration in this repository includes:
* Getting balances from a list of wallet addresses in a .txt
* Accessing transaction data from a single wallet
* Getting all blockchain transactions over a period of time and aggregating the data to get a summary of the blockchain
	
## Scripts:

```get_wallet_balance```:
* A list of wallet addresses (from data/wallet_addresses.txt) are searched though the blockchain and their current balances are populated into a dataframe. 
* The transaction history of a single wallet is extracted from the blockchain and populated into a dataframe.
* This script prints out the results above.

```algorand_transactions```:
* Outputs a csv into /data containing transaction information for the Algorand blockchain over a specified timeframe. Summary values include the total number of transactions, and the different types of transactions.
* Transaction data is requested in batches of one hour increments.

## Set up:
* Install required libraries via ```pip install -r requirements.txt```
* Insert API key and API address in the ```config.py``` file
* Adjust ```START_TIME``` and ```END_TIME``` for the time frame of interest within the ```config.py``` file
* To set up a node, see notes below
	

# Accessing data directly from the Algorand Chain

Direct interaction with the Algorand chain can be achieved by spinning up a containerized node on the network via the Algorand Sandbox. This simplifies the process of creating and configuring a node by using Docker. Sandbox supports operation with private networks (which are only available from the local environment), as well as public networks which allow communication with one of the long running Algorand networks such as mainnet. 
	
### Indexer:

The indexer allows you to search the Algorand Blockchain, and it's main purpose is to provide a set of REST API calls for searching blockchain transactions, accounts, assets and blocks. The REST API's retrieve blockchain data from a PostreSQL compatible database populated using the indexer, which connects to an Algorand node to processes all the ledger data and load the database. The Algorand node it is connected to must also be a 'Archival Node', which has all historical data stored and this makes searching the entire blockchain possible.

	
The indexer itself is not a part of the Algorand node and requires a separate binary download. It allows for the most direct access to the blockchain, but the download process takes a considerable amount of time and resources since the mainnet is approxiametly 4+ tb in size.
* More information: https://developer.algorand.org/docs/get-details/indexer/ - instructions for installing the indexer can be found here: https://developer.algorand.org/docs/run-a-node/setup/indexer/

### Sandbox Setup:

The most efficient way to run a node on Algorand is through the Sandbox, which simplifies the node creation and configuration through Docker. Docker Compose must be installed to do so. 

Additional steps can be found in https://github.com/algorand/sandbox

Quick steps to get started with Sandbox:
* Docker must be installed
* clone the Sandbox from GitHub -> ```git clone https://github.com/algorand/Sandbox.git```
* enter the Sandbox folder -> ```cd Sandbox```
* run the Sandbox executable to start a private network -> ```./Sandbox up mainnet```



