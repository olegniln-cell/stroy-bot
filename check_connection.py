import socket
import sys

HOST = "aws-1-eu-central-1.pooler.supabase.com"
PORT = 5432

try:
    with socket.create_connection((HOST, PORT), timeout=10) as s:
        print(f"✅ Успешно подключились к {HOST} на порту {PORT}")
        sys.exit(0)
except TimeoutError:
    print(f"❌ Не удалось подключиться к {HOST} на порту {PORT}. Время ожидания вышло.")
    print("Это может быть связано с блокировкой файрволом или проблемами с сетью.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Произошла ошибка: {e}")
    print("Возможно, адрес сервера неверный или соединение блокируется.")
    sys.exit(1)
