import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv('TICKETMASTER_API_KEY'))