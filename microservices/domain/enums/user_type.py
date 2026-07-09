from enum import Enum


class UserType(str, Enum):
    VISITOR = "visitor"
    RECRUITER = "recruiter"
    CLIENT = "client"
