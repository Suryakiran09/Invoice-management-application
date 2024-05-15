from storages.backends.azure_storage import AzureStorage

import environ

env = environ.Env()

environ.Env.read_env()
# class AzureMediaStorage(AzureStorage):
#     account_name = env('ACCOUNT_NAME') # Must be replaced by your <storage_account_name>
#     account_key = env('ACCOUNT_KEY') # Must be replaced by your <storage_account_key>
#     azure_container = 'pizzawebstorage'
#     expiration_secs = None
# from storages.backends.azure_storage import AzureStorage

class AzureMediaStorage(AzureStorage):
    location = 'media'
    file_overwrite = False