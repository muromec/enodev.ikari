from models import User
from uuid import uuid4

def setup_root():
    pwd = str(uuid4())[:6]
    user = User(login='root', name='The One')
    user.set_and_encrypt_password(pwd)
    user.save()
    print 'root password', pwd
