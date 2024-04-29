from django.db import models

from db_connection import db

# Create your models here.

neutron_collection = db['Neutron']
selfEmpanelment_collection = db['SelfEmpanelment']


db['SelfEmpanelment'].create_index({"DCID": 1}, unique = True )
db['SelfEmpanelment'].create_index({"TicketID": 1}, unique = True )