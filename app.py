import requests
import socket
import json
import re


def lambda_handler(event, context):
    # Build Variables
    #################
    try:
        api_fqdn = 'fulfilment.unicorn.rentals'
        original_headers = event['headers']
        path = event['path']
    except Exception as e:
        print('Error Building Variables: {}'.format(e))

    # Return Healthcheck
    ####################
    if 'healthcheck' in path:
        body = "Proxy Healthcheck: OK"
        return build_response(200, body)
    
    # DNS Lookup to find real Fulfilment API address
    ################################################
    try:
        dns_lookup = socket.gethostbyname_ex(api_fqdn)
        print(f'PROXY: DNS returned the following values for \'{api_fqdn}\': {dns_lookup}')
        for item in dns_lookup:
            if isinstance(item, list): # Look for lists
                for entry in item: # Search items in lists for API Gateway style fqdns
                    if re.search(r'[a-z0-9]+\.execute-api', entry):
                        api_dns = entry
                        break
                    continue
            elif re.search(r'[a-z0-9]+\.execute-api', item):
                api_dns = item
                break

        api_url = "https://{}".format(api_dns)
        print('PROXY: Built API URL from DNS: {}'.format(api_url))
    except Exception as e:
        body = 'PROXY: Error, Failed to discover the Fulfilment API.  Have you created a VPC Endpoint?: {}'.format(e)
        print(body)
        return build_response(500, body)

    # We're proxying
    # Let's remove some uneeded source headers
    ##########################################
    print(f'PROXY: Incoming (request) Headers: {original_headers}')
    excluded_headers = ['host', 'content-type', 'content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers={key: value for (key, value) in original_headers.items() if key.lower() not in excluded_headers}
    print(f'PROXY: Ougoing (to API) Headers: {headers}')

    # Query String Building
    #######################
    try:
        original_query_strings = event['queryStringParameters']
        query_strings = '?'
        for k, v in original_query_strings.items():
            query_strings += '{}={}&'.format(k, v)
        query_strings = query_strings[:-1]
    except Exception as e:
        body = 'PROXY: Error Building Query Strings: {}'.format(e)
        print(body)
        return build_response(500, body)

    # Final Request Building
    ########################
    try:
        request_url = api_url + path + query_strings
        print(f"PROXY: Sending API Request To: {request_url}")

        incoming_request = requests.request(
            method=event['httpMethod'],
            url=request_url,
            headers=headers,
            allow_redirects=False,
            timeout=10)
            
        # And now handle the response
        #############################
        statuscode = incoming_request.status_code
        request_body = incoming_request.content.decode('utf-8')
        
        print(f'PROXY: Requst Body from Fulfilment API: {request_body}')
        
    except Exception as e:
        body = 'PROXY: Error Accessing Fulfilment API: {}'.format(e)
        print(body)
        return build_response(500, body)

    return build_response(statuscode, request_body)


def build_response(statuscode, body):
    response = {
            "statusCode": statuscode,
            "body": body
            }
    
    return response

