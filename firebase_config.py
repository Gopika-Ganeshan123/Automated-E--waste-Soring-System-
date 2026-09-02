import firebase_admin
from firebase_admin import credentials, firestore, db as rtdb

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://ewaste-sorting-system-default-rtdb.asia-southeast1.firebasedatabase.app/" 

})

# Firestore client
db = firestore.client()

# RTDB reference
rtdb_ref = rtdb.reference("/")
