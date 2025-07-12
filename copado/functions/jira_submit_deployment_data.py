import numpy as np
from simple_salesforce import Salesforce, format_soql
from shlex import quote
import pandas as pd
import os
import requests
import json
from datetime import datetime
from copy import deepcopy

API_VERSION = '60.0'    # SFDX API Version
CHUNK_SIZE = 500        # Chunk size of issues allowed per Deployment payload request
TOKEN_URL = 'https://api.atlassian.com/oauth/token'  # Atlassian Token request URL
DEPLOY_ENDPOINT = 'https://api.atlassian.com/jira/deployments/0.1/cloud/{}/bulk'  # Atlassian Deployment API request URL
DEBUG_MODE = False      # By default, debugging mode is disabled


def get_token(jira_client_id, jira_client_secret):
  """ Using the CLIENT_ID and CLIENT_SECRET from Jira Cloud, 
      obtains and returns the access token for the payload request. """

  # Define the payload (data)
  payload = {
      "audience": "api.atlassian.com",
      "grant_type": "client_credentials",
      "client_id": jira_client_id,
      "client_secret": jira_client_secret
  }

  # Define headers
  headers = {
      'Content-Type': 'application/json'
  }

  # Make the POST request
  response = requests.post(TOKEN_URL, json=payload, headers=headers)

  # Check the response
  if response.status_code == 200:
      return response.json()['access_token']
  else:
      print(f"Error: {response.status_code}")
      print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
      log('Error obtaining access token', error=response.json()['error_description'], data=json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


# log progress
def log(message, error=None, data=None):
    command = 'copado --progress {}'.format(quote(message))
    if error is not None:
        command = command + ' --error-message {}'.format(quote(error))
    if data is not None:
        command = command + ' --result-data {}'.format(quote(data))
    os.system(command)

# process simple-salesforce query results
def sf_api_query(data):
    if data['totalSize'] == 0:
        raise Exception("No data returned.")

    df = pd.DataFrame(data['records']).drop('attributes', axis=1)
    listColumns = list(df.columns)
    for col in listColumns:
        if any (isinstance (df[col].values[i], dict) for i in range(0, len(df[col].values))):
            df = pd.concat([df.drop(columns=[col]),df[col].apply(pd.Series).drop('attributes',axis=1).add_prefix(col+'.')],axis=1)
            new_columns = np.setdiff1d(df.columns, listColumns)
            for i in new_columns:
                listColumns.append(i)
    return df

def get_epoch_time():
    """Get current time in epoch seconds."""
    return int(datetime.now().timestamp())

def get_promo_no(promo_name):
    """Extract deployment sequence number from promotion name."""
    return int(promo_name[1:])

def get_state(promo_status):
    """
    Map Copado Promotion Status to Jira Deployment state.
    enum: unknown, pending, in_progress, cancelled, failed, rolled_back, successful
    """
    return {
        'Scheduled': 'pending',
        'In Progress': 'in_progress',
        'Completed': 'successful',
        'Cancelled': 'cancelled',
        'Completed with errors': 'failed'
    }.get(promo_status, 'unknown')

def get_name(promo):
    """Generate displayName field for the Deployment."""
    source = promo['copado__Source_Environment__r.Name']
    destination = promo['copado__Destination_Environment__r.Name']
    if promo['copado__Back_Promotion__c']:
        return f'{destination} \u276e {source} ({promo["Name"]})'
    else:
        return f'{source} \u276f {destination} ({promo["Name"]})'
    
def get_env_type(env_type):
    """
    Map environment type to Jira environment type.
    enum: unmapped, development, testing, staging, production
    """
    return {
        'development': 'development',
        'testing': 'testing',
        'staging': 'staging',
        'production': 'production'
    }.get(env_type, 'unmapped')

def get_promoted_stories(promotion_id, copa_sf):
    """
    Fetches promoted user stories based on a given promotion ID.

    Args:
        promotion_id (str): The ID of the promotion to fetch user stories for.
        copa_sf (SalesforceConnection): An instance of a Salesforce connection object.

    Returns:
        list: A list of external IDs for the promoted user stories.
    """
    # Define the initial query with placeholders for safe formatting
    query = ("SELECT copado__User_Story__c, "
             "copado__User_Story__r.copadoconnect__External_ID__c, "
             "copado__User_Story__r.copado__Is_Bundle__c "
             "FROM copado__Promoted_User_Story__c "
             "WHERE copado__Promotion__c = {promotion_id}")
    
    # Execute the query using a method that safely formats and executes the SOQL query
    story_df = sf_api_query(copa_sf.query_all(format_soql(query, promotion_id=promotion_id)))

    # Filter non-null External IDs
    external_ids = story_df['copado__User_Story__r.copadoconnect__External_ID__c'].dropna().tolist()

    # Filter stories that are bundles
    bundle_df = story_df[story_df['copado__User_Story__r.copado__Is_Bundle__c']]
    bundle_list = bundle_df['copado__User_Story__c'].tolist()

    # Get bundled user stories with non-null external ID
    if bundle_list:
        bundle_query = ("SELECT copado__User_Story__r.copadoconnect__External_ID__c "
                        "FROM copado__Bundled_Story__c "
                        "WHERE copado__User_Story__r.copadoconnect__External_ID__c != null "
                        "AND copado__Package_Version__r.copado__User_Story__c IN {bundle_list}")
        
        # Execute the query for bundled stories
        bundled_external_ids = sf_api_query(copa_sf.query_all(format_soql(bundle_query, bundle_list=bundle_list)))
        bundled_external_ids = bundled_external_ids['copado__User_Story__r.copadoconnect__External_ID__c'].dropna().tolist()

        # Combine the lists of external IDs
        external_ids += bundled_external_ids

    return external_ids

def chunk(lst, chunk_size=500):
    # Using list comprehension to split the list into chunks of {chunk_size}
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def get_deployments(stories_list, promo_no, payload):
    deployments = []
    i = 0
    for c in chunk(stories_list, CHUNK_SIZE):
        pl = deepcopy(payload)
        pl["associations"][0]["values"] = c
        pl["deploymentSequenceNumber"] = promo_no * 10 + i
        deployments.append(pl)
        i += 1
    return deployments

def main():
    # @param (global)
    COPA_ENDPOINT = os.environ['CF_SF_ENDPOINT']
    COPA_SESSION = os.environ['CF_SF_SESSIONID']

    # @param (function parameters)
    # https://<your-jira-instance>.atlassian.net/_edge/tenant_info
    JIRA_CLOUD_ID = os.environ['JIRA_CLOUD_ID']

    # Define your client ID and client secret
    # https://<your-jira-instance>.atlassian.net/secure/admin/oauth-credentials
    JIRA_CLIENT_ID = os.environ['JIRA_CLIENT_ID']
    JIRA_CLIENT_SECRET = os.environ['JIRA_CLIENT_SECRET']

    JIRA_ENDPOINT = DEPLOY_ENDPOINT.format(JIRA_CLOUD_ID)
    JIRA_TOKEN = get_token(JIRA_CLIENT_ID, JIRA_CLIENT_SECRET)

    PROMOTION_ID = os.environ['PROMOTION_ID']
    DEST_ENV_TYPE = os.environ['DEST_ENV_TYPE'].lower()

    # @param DEBUG_MODE
    if os.environ['DEBUG_MODE'].lower() in ['true', '1', 't', 'y', 'yes']:
        DEBUG_MODE = True
        log('DEBUG_MODE is ON')
    else:
        DEBUG_MODE = False

    if DEBUG_MODE:
        print('PROMOTION_ID = ' + PROMOTION_ID)
        print('DEST_ENV_TYPE = ' + DEST_ENV_TYPE)

    #connect to salesforce (Copado org)
    copa_sf = Salesforce(instance_url=COPA_ENDPOINT, session_id=COPA_SESSION, version=API_VERSION)

    # get promotion data (Name, Source, Dest Env, Dest Env Name, Dest Env Type, IsBackPromotion, Pipeline ID, Pipeline Name, Status,)
    # build soql query
    query = ('Select Id, Name, copado__Source_Environment__r.Name, copado__Destination_Environment__c, copado__Destination_Environment__r.Name, '
            'copado__Back_Promotion__c, copado__Project__r.copado__Deployment_Flow__c, '
            'copado__Project__r.copado__Deployment_Flow__r.Name, copado__Pipeline__c, copado__Pipeline__r.Name, '
            'copado__Status__c, LastModifiedDate FROM copado__Promotion__c '
            'WHERE Id = {promotion_id}')
    promo_df = sf_api_query(copa_sf.query_all(format_soql(query, promotion_id=PROMOTION_ID))).to_dict('records')[0]

    pipeline_id   = (
        promo_df.get('copado__Pipeline__c')
        or promo_df.get('copado__Project__r.copado__Deployment_Flow__c')
    )
    pipeline_name = (
        promo_df.get('copado__Pipeline__r.Name')
        or promo_df.get('copado__Project__r.copado__Deployment_Flow__r.Name')
    )

    promotion_no = get_promo_no(promo_df['Name'])
    promoted_stories_lst = get_promoted_stories(PROMOTION_ID, copa_sf)

    if len(promoted_stories_lst) == 0:
        log('No Stories in Promotion have Jira Keys')
        return
    
    # bail out if absolutely nothing was found
    if not pipeline_id:
        log(f"No pipeline or deployment-flow on Promotion {PROMOTION_ID}")
        return

    deployment_payload = {
        "deploymentSequenceNumber": None,
        "updateSequenceNumber": get_epoch_time(),
        "associations": [
            {
                "associationType": "issueIdOrKeys",
                "values": None
            }
        ],
        "displayName": get_name(promo_df)[:255],
        "description": '{}: {} to {}'.format(promo_df['Name'], promo_df['copado__Source_Environment__r.Name'], promo_df['copado__Destination_Environment__r.Name']),
        "url": COPA_ENDPOINT + "/" + promo_df['Id'],
        "lastUpdated": datetime.strptime(promo_df['LastModifiedDate'], "%Y-%m-%dT%H:%M:%S.%f%z").isoformat(),
        "state": get_state(promo_df['copado__Status__c']),
        "pipeline": {
            "id": pipeline_id,
            "displayName": pipeline_name,
            "url": COPA_ENDPOINT + "/" + pipeline_id
        },
        "environment": {
            "id": promo_df['copado__Destination_Environment__c'],
            "displayName": promo_df['copado__Destination_Environment__r.Name'],
            "type": get_env_type(DEST_ENV_TYPE)
        },
        "schemaVersion": "1.0"
    }

    if DEBUG_MODE:
        print(json.dumps(json.loads(deployment_payload), indent=4, separators=(",", ": ")))

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + JIRA_TOKEN
    }

    payload = json.dumps( {
        "properties": {},
        "deployments": get_deployments(promoted_stories_lst, promotion_no, deployment_payload),
        "providerMetadata": {
            "product": "Copado Deployer"
        }
    } )

    if DEBUG_MODE:
        print(json.dumps(json.loads(payload), indent=4, separators=(",", ": ")))

    response = requests.request(
        "POST",
        JIRA_ENDPOINT,
        data=payload,
        headers=headers
    )

    if DEBUG_MODE:
        print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

    # Check the response
    if response.status_code == 202:
        print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        log('Successful Deployment API callout', data=json.dumps(json.loads(response.text), indent=4, separators=(",", ": ")))
    else:
        print(f"Error: {response.status_code}")
        print(json.dumps(json.loads(response.text), indent=4, separators=(",", ": ")))
        log('Error in Deployment API callout', error='Error in Deployment API callout', data=json.dumps(json.loads(response.text), indent=4, separators=(",", ": ")))


if __name__ == "__main__":
    main()