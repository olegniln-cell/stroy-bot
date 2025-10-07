# Создайте файл scripts/populate_test_data.py
from models import User, Company  # Теперь импорт соответствует структуре
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
session = Session()


def populate_data():
    # Создаем тестового пользователя
    test_user = User(username="test_user", email="test@example.com", role="user")

    # Создаем тестовую компанию
    test_company = Company(name="Test Company", created_by=test_user)

    session.add(test_user)
    session.add(test_company)
    session.commit()


if __name__ == "__main__":
    populate_data()
