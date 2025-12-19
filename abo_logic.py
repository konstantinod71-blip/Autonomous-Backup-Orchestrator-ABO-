import os
import datetime
import sys

# ==========================================
# КОНФИГУРАЦИЯ СИСТЕМЫ ABO
# ==========================================
SOURCE_VM = "knst@192.168.64.6"    # VM1: Источник данных
STORAGE_VM = "knst@192.168.64.7"   # VM2: Хранилище бэкапов

SOURCE_PATH = "~/my_data"         
GPG_PASSPHRASE = "ABO_Strong_2025" # Пароль для AES-256
# ==========================================

def run_orchestration():
    print(f"\n{'='*45}")
    print("🚀 AUTONOMOUS BACKUP ORCHESTRATOR (ABO) v1.0")
    print(f"{'='*45}")

    # 1. Генерация имени файла
    timestamp = datetime.datetime.now().strftime("%Y-%m-d_%H-%M-%S")
    filename = f"abo_encrypted_backup_{timestamp}.tar.gz.gpg"
    
    print(f"[*] Цель: {SOURCE_VM}:{SOURCE_PATH}")
    print(f"[*] Назначение: {STORAGE_VM}:~/backups/")

    # 2. Проверка доступности VM1 (Агента)
    print("\n[1/3] Проверка связи с Агентом (VM1)...")
    check_source = os.system(f"ssh -o ConnectTimeout=5 {SOURCE_VM} 'ls {SOURCE_PATH} > /dev/null'")
    if check_source != 0:
        print("❌ ОШИБКА: VM1 недоступна или папка не существует!")
        return

    # 3. Подготовка хранилища на VM2
    print("[2/3] Подготовка изолированного хранилища (VM2)...")
    os.system(f"ssh {STORAGE_VM} 'mkdir -p ~/backups'")

    # 4.Сжатие + Шифрование + Передача
    # Данные шифруются ДО того, как попадут в сеть или на вторую ВМ
    print("[3/3] Запуск шифрования (AES-256) и передачи данных...")
    
    # Конвейер: tar (сжать) -> gpg (зашифровать) -> ssh (передать)
    backup_cmd = (
        f"ssh {SOURCE_VM} 'tar -cz -C {SOURCE_PATH} . | "
        f"gpg --batch --yes --passphrase {GPG_PASSPHRASE} -c' | "
        f"ssh {STORAGE_VM} 'cat > ~/backups/{filename}'"
    )
    
    status = os.system(backup_cmd)

    if status == 0:
        print(f"\n✅ УСПЕХ: Данные оркестрованы и защищены.")
        print(f"📎 Файл на VM2: ~/backups/{filename}")
        
        # правило 3-2-1: Копия на Orchestrator (Mac)
        print(f"📦 Создание локальной избыточной копии на Mac...")
        os.system(f"scp {STORAGE_VM}:~/backups/{filename} ./local_copy_{filename}")
        print(f"📂 Локальный путь: {os.getcwd()}/local_copy_{filename}")
    else:
        print("\n❌ КРИТИЧЕСКИЙ СБОЙ: Поток данных прерван. Проверьте SSH-ключи!")

if __name__ == "__main__":
    try:
        run_orchestration()
    except KeyboardInterrupt:
        print("\n🛑 Процесс прерван пользователем.")
        sys.exit()
