# Project Architecture

```
app/
├── main.py                 #FastAPI app initialization
├── dependencies.py         #Dependency injection
├── config.py               #Settings
├── models/                 #SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   └── product.py
├── schemas/               #Pydantic models
│   ├── __init__.py
│   ├── user.py
│   └── product.py
├── services/              #Business logic
│   ├── __init__.py
│   ├── user_service.py
│   └── product_service.py
├── repositories/          #Data access layer (CRUD)
│   ├── __init__.py
│   └── user_repository.py
├── routers/              #API routes
│   ├── __init__.py
│   ├── users.py
│   └── products.py
├── core/                 #Core utilities
│   ├── __init__.py
│   ├── security.py
│   └── database.py
└── tests/
    └── ...
```

