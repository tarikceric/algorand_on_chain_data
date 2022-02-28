from algosdk.v2client import indexer
import os
import pandas as pd
import yaml
import sys
import algosdk
import time
from dateutil.rrule import HOURLY, rrule
from dateutil.parser import parse


def load_config(config_file):
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
        headers = {"X-API-KEY": config['X-API-KEY'], }
    indexer_client = indexer.IndexerClient(token, url, headers)
    try:
        indexer_client.health()
    except (TypeError, algosdk.error.IndexerHTTPError) as e:
        print(f"Indexer not properly connected: {e}")
        sys.exit(1)

    return indexer_client


def get_transaction_response(indexer_client, config):
    """
    Returns all transactions from the blockchain between a time period specified in the config file. This retrieves the
    max number of transaction per request (1000), and the 'next token' is used to pick up where the last search ended

    :param indexer_client: indexer client object
    :param config: configuration file for start/end times
    """

    start_time = config['START_TIME']
    end_time = config["END_TIME"]

    nexttoken = ""
    numtx = 1

    responses = []

    while numtx > 0:
        # each request returns 1000 transactions

        try:
            response = indexer_client.search_transactions(start_time=start_time, end_time=end_time,
                                                          next_page=nexttoken, limit=1000)
        except algosdk.error.IndexerHTTPError as e:
            print(f"Attempt to adjust batch size: {e}")
            sys.exit(1)

        transactions = response['transactions']
        responses += transactions
        numtx = len(transactions)
        # the 'next token' is added to the result list which allows querying of the next 1000 transactions
        if numtx > 0:
            nexttoken = response['next-token']
    return responses


def get_transaction_in_chunks(config, indexer_client):
    """
    Splits the timeframe into 1 hour segments for requesting the addreses. This accounts for limitations on the
     number of requests and the duration which may result in time-out errors.

    """

    # Get the date to proper format
    start = config['START_TIME'][:-6]
    end = config['END_TIME'][:-6]
    chars_to_remove = ["-", ":"]
    for char in chars_to_remove:
        start = start.replace(char, "")
        end = end.replace(char, "")

    # create a list of dates between start date and end date with 1 hours intervals
    dates = list(rrule(HOURLY,
                       dtstart=parse(start),
                       until=parse(end),
                       interval=1))

    responses = []

    for start, end in zip(dates[:-1], dates[1:]):
        print(f"Retrieving transactions from {start} to {end}")
        responses += get_transaction_response(indexer_client, config)
    df = pd.DataFrame(responses)

    return df


def clean_dataframe(df):
    """
    Extracts dict fields into their own columns and cleans up the dataframe.

    :param df: A dataframe of address query responses
    """

    df = pd.concat([df.drop(['asset-transfer-transaction'], axis=1),
                    df['asset-transfer-transaction'].apply(pd.Series)
                   .add_suffix('-asset-transfer-tx').drop(['0-asset-transfer-tx'], axis=1, errors='ignore')], axis=1)

    df = pd.concat([df.drop(['payment-transaction'], axis=1),
                    df['payment-transaction'].apply(pd.Series)
                   .add_suffix('-payment-tx').drop(['0-payment-tx'], axis=1, errors='ignore')], axis=1)

    df = pd.concat([df.drop(['application-transaction'], axis=1),
                    df['application-transaction'].apply(pd.Series)
                   .add_suffix('-application-tx').drop(['0-application-tx'], axis=1, errors='ignore')], axis=1)

    return df


def blockchain_timeframe_summary(final_df, config):
    """
    Get summary statistics

    :param final_df: The full dataframe of address information from the blockchain
    :param config: configuration file for including start/end times in output dataframe
    """

    print("Getting summary counts of analysis")
    summary = {'total_transactions': len(final_df),
               'from_time': config['START_TIME'],
               'to_time': config['END_TIME'],
               'count_unique_assets': final_df['asset-id-asset-transfer-tx'].nunique(),
               'count_unique_applications': final_df['application-id-application-tx'].nunique()}

    tx_type_summary = final_df['tx-type'].value_counts().to_dict()
    summary.update(tx_type_summary)
    return summary


def write_summary_to_csv(summary_dict):
    """
    :param summary_dict: the dictionary object with aggregate transaction data for the blockchain
    """

    cur_path = os.path.abspath(os.path.dirname(__file__))
    rel_path = "data/"
    output_folder = os.path.abspath(os.path.join(cur_path, rel_path))

    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = "algorand-transactions-summary-" + timestr + '.csv'

    if os.path.exists(output_folder):
        print(f"Outputing summary csv to {output_folder}")
        with open(os.path.join(output_folder, file_name), 'w') as f:
            for key in summary_dict.keys():
                f.write("%s,%s\n"%(key, summary_dict[key]))

    else:
        print("Folder for output data is missing")


def main():
    config = load_config('config.yml')

    indexer_client = connect(config)

    tx_responses = get_transaction_in_chunks(config, indexer_client)

    tx_data_df = clean_dataframe(tx_responses)

    summary = blockchain_timeframe_summary(tx_data_df, config)

    write_summary_to_csv(summary)


if __name__ == "__main__":
    main()
