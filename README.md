# Project Architecture

```
app/
├── main.py                 #FastAPI app initialization
├── dependencies.py         #Dependency injection
├── config.py               #Settings
├── models/                 #SQLAlchemy models
│   ├── __init__.py
│   ├── property.py
│   └── property_image.py
├── schemas/               #Pydantic models
│   ├── __init__.py
│   ├── property.py
│   └── property_image.py
├── services/              #Business logic
│   ├── __init__.py
│   ├── property_service.py
│   └── product_image_service.py
├── repositories/          #Data access layer (CRUD)
│   ├── __init__.py
│   └── property_repository.py
│   └── property_image_repository.py
├── routers/              #API routes
│   ├── __init__.py
│   ├── properties.py
│   └── property_images.py
├── core/                 #Core utilities
│   ├── __init__.py
│   ├── security.py
│   └── database.py
└── tests/
    └── ...
```

