from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('api_key'))

models = client.models.list()
for m in models.data:
    print(m.id)