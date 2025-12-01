import bcrypt

# przykładowy użytkownik admin
admin_password = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": admin_password,
        "roles": "ROLE_ADMIN"
    }
}
