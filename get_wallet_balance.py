from algosdk.v2client import indexer
import os
import pandas as pd
import yaml
import sys
import algosdk


def load_config(config_file: str) -> dict:
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


def connect(config) -> indexer.IndexerClient:
    """
    Connect to the Indexer client to access data on a node
    """
    url = config['URL']
    token = config['TOKEN']
    headers = ""
    if config['X-API-KEY']:
        headers = {"X-API-KEY": config['X-API-KEY'], }
    indexer_client = indexer.IndexerClient(token, url, headers)
    try:
        indexer_client.health()
    except (TypeError, algosdk.error.IndexerHTTPError) as e:
        print(f"Indexer not properly connected - check config file: {e}")
        sys.exit(1)

    return indexer_client


def read_txt() -> list:
    """
    Access a .txt file included in the project folder
    """
    cur_path = os.path.abspath(os.path.dirname(__file__))
    rel_path = "data/wallet_addresses.txt"
    txt_path = os.path.abspath(os.path.join(cur_path, rel_path))

    with open(txt_path, 'r') as f:
        return f.read().splitlines()


def get_wallet_balances(indexer_client, addresses) -> pd.DataFrame:
    """
    Access a list of Algorand wallet addresses and return a dataframe with their balances

    :param indexer_client: indexer client object
    :param addresses: text file of Algorand addresses
    """
    df = pd.DataFrame()
    # Initialize an empty list to store incorrect addresses
    invalid_address = []
    for address in addresses:
        try:
            # get the asset holdings
            print(f"Retrieving data for Algorand wallet : {address}")
            response = indexer_client.account_info(address=address)
        except algosdk.error.IndexerHTTPError as e:
            # if there is an error with a wallet, store it in the 'invalid_address' list
            print(f"{e}")
            invalid_address.append(address)
            print('Logging and proceeding to next address')
            continue
        else:
            # Extract only the total algo balance
            # Balances are converted from Microalgo to Algo (10^6)
            balance = response['account']['amount'] / (10 ** 6)
            df = pd.concat([df, pd.DataFrame([{'account': address, 'balance': balance}])])
    return df


def transaction_history(indexer_client, addresses, config) -> pd.DataFrame:
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
        print(f"{wallet_address} is an invalid address: {e}")
        sys.exit(1)

    # extract specific fields from the response and insert into a dataframe
    for x in response['transactions']:
        tx_amount = x['payment-transaction']['amount']
        tx_id = x['id']
        receiver = x['payment-transaction']['receiver']
        sender = x['sender']
        temp_df = pd.DataFrame([{'Tx Amount': tx_amount, 'Tx Id': tx_id, 'Receiver': receiver, 'Sender': sender}])
        df = pd.concat([df, temp_df])
    return df


def main():
    config = load_config('config.yml')

    indexer_client = connect(config)

    address_list = read_txt()

    wallet_info_df = get_wallet_balances(indexer_client, address_list)

    transaction_history_df = transaction_history(indexer_client, address_list, config)

    print("Wallet data for specified address\n" + wallet_info_df.to_string())
    print("Transaction data for single wallet\n" + transaction_history_df.to_string())


if __name__ == "__main__":
    main()
