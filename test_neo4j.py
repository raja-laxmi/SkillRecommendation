from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv(override=True)

uri = os.getenv("COGNODB_URI")
username = os.getenv("COGNODB_USERNAME")
password = os.getenv("COGNODB_PASSWORD")

print("URI:", uri)
print("USER:", username)
print("PASSWORD LOADED:", bool(password))
print("PASSWORD LENGTH:", len(password or ""))

driver = GraphDatabase.driver(
    uri,
    auth=(username, password)
)

driver.verify_connectivity()
print("NEO4J CONNECTION SUCCESS")

driver.close()