
# pankaj developer account
# PATH_TO_PRIVATE_KEY_FILE = "private.key"

# Anil admin demo account
PATH_TO_PRIVATE_KEY_FILE = "private-admin-demo.key"

with open(PATH_TO_PRIVATE_KEY_FILE) as private_key_file:
    private_key = private_key_file.read()

PRIVATE_KEY = private_key