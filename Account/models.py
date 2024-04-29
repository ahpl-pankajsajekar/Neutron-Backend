from django.db import models

from db_connection import db

# Create your models here.
selfEmpanelmentCollection =  db['Neutron']
UserMasterCollection =  db['UserMaster']

db['UserMaster'].create_index([("email", 1)], unique=True)
