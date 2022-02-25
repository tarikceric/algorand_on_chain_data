from algosdk.v2client import indexer
import os
import pandas as pd
import yaml
import sys
import algosdk
import urllib

def loadConfig(config_file):
    """
    Function to load yaml configuration file
    :param config_file: name of config file in directory
    """
    try:
        with open(config_file) as file:
            config = yaml.safe_load(file)
    except IOError as e:
        print(e)
        sys.exit(1)

    return config

def connect(config):
    """
    Connect to the Indexer client to access data on a node
    """
    url = config['URL']
    token = config['TOKEN']
    headers = ""
    if config['X-API-KEY']:
        headers = {"X-API-KEY": config['X-API-KEY'],}
    indexer_client = indexer.IndexerClient(token, url, headers)
    try:
        indexer_client.health()
    except urllib.error.URLError as e:
        print(f"Indexer not properly connected - check config file: {e}")
        sys.exit(1)

    return indexer_client


def read_txt ():
    """
    Access a .txt file included in the project folder
    """
    cur_path = os.path.abspath(os.path.dirname(__file__))
    rel_path = "data/wallet_addresses.txt"
    txt_path = os.path.abspath(os.path.join(cur_path, rel_path))

    with open(txt_path, 'r') as f:
        return f.read().splitlines()


def get_wallet_balances(indexer_client, addresses):
    """
    Access a list of Algorand wallet addresses and return a dataframe with their balances

    :param indexer_client: indexer client object
    :param addresses: text file of Algorand addresses
    """
    df = pd.DataFrame()
    for address in addresses:
        #If 5 consecutive addresses return an error then source dataset must be checked
        for attempt in range(5):
            try:
                print(f"Retrieving data for Algorand wallet : {address}")
                response = indexer_client.account_info(address=address)
            # get the asset holdings
            except algosdk.error.IndexerHTTPError as e:
                print(f"{e}")
                print('Logging and proceeding to next address')
            else:
                break
        else:
            print("5 consecutive addresses failed to read - check data source")
            sys.exit(1)

        # Extract only the total algo balance
        # Balances are converted from Microalgo to Algo (10^6)
        balance = response['account']['amount'] / (10**6)
        df=df.append({'account': address, 'balance': balance}, ignore_index=True)
    return df

def transactionHistory(indexer_client, addresses, config):
    """
    Access the first wallet in a text file of Algorand wallet addresses and return a dataframe with transaction history
    at a specified start time.

    :param indexer_client: indexer client object
    :param addresses: text file of Algorand addresses
    :param config: configuration file
    """

    start_time = config['START_TIME']
    wallet_address = addresses[0]
    df = pd.DataFrame()

    try:
        print(f"Retrieving transaction data for wallet {wallet_address} beginning at {start_time}")
        response = indexer_client.search_transactions_by_address(address=wallet_address, start_time=start_time)
    except algosdk.error.IndexerHTTPError as e:
        return e

    #extract specific fields from the response and insert into a dataframe
    for x in response['transactions']:
        txAmount = x['payment-transaction']['amount']
        txId = x['id']
        receiver = x['payment-transaction']['receiver']
        sender = x['sender']
        temp_df = pd.DataFrame([{'Tx Amount': txAmount, 'Tx Id': txId, 'Reciever': receiver, 'Sender': sender}])
        df = pd.concat([df, temp_df])
    return df


def main():

    config = loadConfig('config.yml')

    indexer_client = connect(config)

    address_list = read_txt()

    wallet_info_df = get_wallet_balances(indexer_client, address_list)

    transaction_history_df = transactionHistory(indexer_client, address_list, config)

    print("Wallet data for specified address\n" + wallet_info_df.to_string())
    print("Transaction data for single wallet\n" + transaction_history_df.to_string())

main()

if __name__ == "__main__":
    main()
