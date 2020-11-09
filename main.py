import os, requests, uuid, asyncio
from sfmc import SFMC
from minio_storage import BLOB

# Get secrets and store as variables
response = requests.get("https://mgti-dal-so-vlt.mrshmc.com/v1/kv/data/oss2/owg-sfmc-connector", headers={"X-Vault-Token": os.environ['VAULT_TOKEN'], "X-Vault-Namespace": "OCIO-POC-Vault"})
if response.status_code != 200:
    raise Exception("Unable to fetch secrets - ", response.content)
secrets = response.json()['data']['data']

# Run the job
id = uuid.uuid4()
sfmc = SFMC(secrets['sfmc_org_id'], secrets['sfmc_client_id'], secrets['sfmc_client_secret'])
store = BLOB(secrets['connection_string'], secrets['container_name'])
blob_name, df = sfmc.run_week(id, 0)
store.write(df, blob_name)
print('Successful run', id)
