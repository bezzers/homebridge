import requests
import asyncio
import pandas as pd
import pyarrow as pa
import xmltodict
import json
import datetime
from functools import partial

class SFMC:
    def __init__(self, org_id, client_id, client_secret):
        self.org_id = org_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self.get_token()

    # Gets the SFMC authorization token
    def get_token(self):
        url = f'https://{self.org_id}.auth.marketingcloudapis.com/v1/requestToken'
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, json={'clientId': self.client_id, 'clientSecret': self.client_secret})
        if response.status_code != 200:
            raise Exception("Failed to retrieve SFMC token")
        token = response.json()['accessToken']
        return token

    # Makes one SOAP request filtered to a particular date range
    async def make_soap_request(self, object_type, start_date, end_date, request_id):
        url = f'https://{self.org_id}.soap.marketingcloudapis.com/Service.asmx'
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
        <s:Header>
            <fueloauth>{self.token}</fueloauth>
        </s:Header>
        <s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <RetrieveRequestMsg xmlns="http://exacttarget.com/wsdl/partnerAPI">
                <RetrieveRequest>
                    <ContinueRequest>{request_id}</ContinueRequest>
                    <ObjectType>{object_type}</ObjectType>
                    <Properties>EventType</Properties>
                    <Properties>SubscriberKey</Properties>
                    <Properties>SendID</Properties>
                    <Properties>EventDate</Properties>
                    <Filter xsi:type="ns1:SimpleFilterPart" xmlns:ns1="http://exacttarget.com/wsdl/partnerAPI">
                    <Property>EventDate</Property>
                    <SimpleOperator>between</SimpleOperator>
                    <DateValue>{start_date}</DateValue>
                    <DateValue>{end_date}</DateValue>
                    </Filter>
                </RetrieveRequest>
            </RetrieveRequestMsg>
        </s:Body>
        </s:Envelope>
        """
        loop = asyncio.get_event_loop()
        post = partial(requests.post, headers={"Content-Type": "text/xml", "SOAPAction": "Retrieve"}, data=body)
        response = await loop.run_in_executor(None, post, url)
        return response

    # Fetches all of the results for a particular set of filters by making repeated requests
    async def fetch_all_results(self, object_type, start_date, end_date, df):
        request_id, status = "", None
        while status != 'OK':
            response = await self.make_soap_request(object_type, start_date, end_date, request_id)
            if response.status_code != 200:
                raise Exception('SOAP request failed - ', response.content)
            response_dict = xmltodict.parse(response.content)
            res = response_dict['soap:Envelope']['soap:Body']['RetrieveResponseMsg']
            request_id = res['RequestID']
            status = res['OverallStatus']
            data = res['Results']
            df = df.append(data)
            print('Fetched', object_type, start_date, len(df), id)
        return df[['EventType', 'SendID', 'SubscriberKey', 'EventDate']]

    # Returns the dates for the Monday and Sunday of the week [offset] weeks back from today
    def get_filter_dates(self, date, offset=0):
        dow = date.weekday()
        monday = date - datetime.timedelta(days=dow + 7 * (offset + 1))
        sunday = monday + datetime.timedelta(days=7)
        return monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')
        
    # Runs the queries for one week and amalgamates the results
    async def run_week(self, id, offset=0):
        start_date, end_date = self.get_filter_dates(datetime.datetime.today(), offset)

        # Runs each event type in parallel
        def fetch(event):
            return self.fetch_all_results(event, start_date, end_date, pd.DataFrame())
        events = ['SentEvent', 'OpenEvent', 'ClickEvent', 'BounceEvent', 'UnsubEvent']
        reqs = list(map(fetch, events))
        res = await asyncio.gather(*reqs)
        df = pd.DataFrame()
        for d in res:
            df = df.append(d)
            d = None

        # Group and write to a parquet file
        return 'events-' + start_date, df
