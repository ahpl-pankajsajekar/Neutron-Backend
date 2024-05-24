import pymongo

# url = 'mongodb://localhost:27017'
url = 'mongodb+srv://pankajsajekar:KNVrOACdk7sToid5@neutroncluster.lvsh062.mongodb.net/'

client = pymongo.MongoClient(url)

# db = client['test_mongo']  # locally
db = client['ProviderPortalDatabase'] # atlas