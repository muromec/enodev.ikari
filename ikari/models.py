from hopak import models
from flaskext.auth import AuthUser

class User(models.Model, AuthUser):
    def __getstate__(self):
        return {
                "login": self.login,
        }

    __key__ = ('login',)

class Project(models.Model):
    __key__ = ('name',)
