from database.models import UserModel

def main():
    user_model = UserModel()
    if user_model.clear_logs():
        print("✅ Tabela logów została wyczyszczona pomyślnie.")
    else:
        print("❌ Wystąpił błąd podczas czyszczenia logów.")

if __name__ == "__main__":
    main() 