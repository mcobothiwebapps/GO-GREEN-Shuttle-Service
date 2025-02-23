import pyrebase

config = {
            "apiKey": "AIzaSyBqBG5XCNeeUMkCZVQPxM5W9drsh3r3g4Q",
            "authDomain": "shuttle-service-55877.firebaseapp.com",
            "databaseURL": "https://shuttle-service-55877-default-rtdb.firebaseio.com/",
            "projectId": "shuttle-service-55877",
            "storageBucket": "shuttle-service-55877.appspot.com",
            "messagingSenderId": "552668538344",
            "appId": "1:552668538344:web:a118828527472b1743305d"
        }

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
database = firebase.database()
