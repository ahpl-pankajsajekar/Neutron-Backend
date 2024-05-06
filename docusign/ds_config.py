
PATH_TO_PRIVATE_KEY_FILE = "private.key"

with open(PATH_TO_PRIVATE_KEY_FILE) as private_key_file:
    private_key = private_key_file.read()

PRIVATE_KEY = private_key