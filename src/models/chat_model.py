from pydantic import Basemodel
from fastapi import validator

class Chatmodel(Basemodel):
    message: str