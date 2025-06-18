import asyncio
import json
import aiohttp
from volcano_api import VolcanoAPIClient


# Example: Asynchronous call
async def volcano_api_async_example():
    """Volcano Engine API Asynchronous Call Example"""
    # Initialize client side
    client = VolcanoAPIClient(
        access_key_id="AKLTNjgyYzQ2MTQ4NTE5NGQwZjg1ZTU3NDAzMDVkOTUyMzU",
        secret_access_key="TmpBNU5UVm1NMkkyTmpNeE5HWmtaR0prTXpJNU9EVTBOekZpWVRFMlpXVQ=="
    )
    
    # The asynchronous call API lists the underlying model
    response = await client.request_async(
        action="ListFoundationModelVersions",
        payload={
            "FoundationModelName": "doubao-1-5-ui-tars"
        },  # If there are any required request parameters, you can add them here.
    )
    
    print("Result of asynchronous call:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    return response

# Example of usage in a Fast API application
'''FastAPI import from fastAPI, Depends
From volcano_api import VolcanoAPIClient

App = FastAPI ()

#Dependency injection, create client side
Def get_volcano_client ():
Returns VolcanoAPIClient (
access_key_id = "AKLTNjgyYzQ2MTQ4NTE5NGQwZjg1ZTU3NDAzMDVkOTUyMzU",
secret_access_key = "TmpBNU5UVm1NMkkyTmpNeE5HWmtaR0prTXpJNU9EVTBOekZpWVRFMlpXVQ=="
)

@App.get ("/models")
Async def list_models (client: VolcanoAPIClient = Depends (get_volcano_client)):
#Asynchronous call API
Response = await client. request_async (
Action = "ListFoundationModels",
Payload = {}
)
Return response'''

# test run
if __name__ == "__main__":
    # Running the asynchronous call example
    asyncio.run(volcano_api_async_example())