import pymongo
import certifi
ca = certifi.where()
 
try:
    # url = 'mongodb://localhost:27017'
    # client = pymongo.MongoClient(url)
    # db = client['test_mongo']  # local
    
    url = 'mongodb+srv://pankajsajekar:KNVrOACdk7sToid5@neutroncluster.lvsh062.mongodb.net/'
    client = pymongo.MongoClient(url, tlsCAFile=ca)
    db = client['ProviderPortalDatabase'] # atlas
    
except Exception as e:
    print(e)