# -*- coding: utf-8 -*-
import os


def collect_code(paths_to_include, output_file):
    """
    Собирает содержимое только из указанных файлов и папок.
    """
    with open(output_file, "w", encoding="utf-8") as outfile:
        processed_paths = set()

        for item_path in paths_to_include:
            if not os.path.exists(item_path):
                print("Путь не найден: {}".format(item_path))
                continue

            if os.path.isdir(item_path):
                # Если это папка, рекурсивно обходим ее
                for dirpath, _, filenames in os.walk(item_path):
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        if file_path not in processed_paths and filename.endswith(
                            ".py"
                        ):
                            process_file(file_path, outfile)
                            processed_paths.add(file_path)
            elif os.path.isfile(item_path):
                # Если это файл, обрабатываем его
                if item_path not in processed_paths and item_path.endswith(".py"):
                    process_file(item_path, outfile)
                    processed_paths.add(item_path)
            else:
                print("Пропускаю: {} (не является файлом или папкой)".format(item_path))


def process_file(file_path, outfile):
    """
    Открывает и записывает содержимое одного файла.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as infile:
            content = infile.read()
            outfile.write("\n# --- File: {} ---\n\n".format(file_path))
            outfile.write(content)
            outfile.write("\n")
    except Exception as e:
        print("Не удалось прочитать файл {}: {}".format(file_path, e))


if __name__ == "__main__":
    # --- Измените этот список ---
    files_to_collect = [
        "README.md",
        "main.py",
        "middlewares/role_checker.py",
        "middlewares/db_middleware.py",
        "middlewares/company_middleware.py",
        "middlewares/subscription_checker.py",
        "middlewares/audit_middleware.py",
        "handlers/start.py",
        "handlers/company.py",
        "handlers/tasks.py",
        "handlers/user.py",
        "handlers/file_upload.py",
        "handlers/projects.py",
        "handlers/reports.py",
        "handlers/invite.py",
        "handlers/reassign.py",
        "handlers/status.py",
        "handlers/help.py",
        "handlers/files.py",
        "handlers/admin_billing.py",
        "handlers/important_stuff.py",
        "handlers/payments.py",
        "handlers/admin.py",
        "handlers/__init__.py",
        "models/file.py",
        "models/user.py",
        "models/project.py",
        "models/task.py",
        "models/company.py",
        "models/subscription.py",
        "models/trial.py",
        "models/plan.py",
        "models/session.py",
        "models/invoice.py",
        "models/payment.py",
        "models/base.py",
        "models/__init__.py",
        "models/audit_log.py",
        "services/companies.py",
        "services/projects.py",
        "services/tasks.py",
        "services/users.py",
        "services/reports.py",
        "services/files.py",
        "services/subscriptions.py",
        "services/notify_jobs.py",
        "services/payments.py",
        "services/import_export.py",
        "services/audit.py",
        "services/test_s3.py",
        "utils/helpers.py",
        "utils/decorators.py",
        "utils/keyboards.py",
        "utils/enums.py",
        "utils/subscription_check.py",
        "scripts/README.md",
        "scripts/check_models_vs_db.py",
        "scripts/seed.py",
        "scripts/check_seed.py",
        "scripts/test_s3.py",
        "scripts/clear_s3.py",
        "scripts/setup_s3_lifecycle.py",
        "scripts/compress_and_archive.py",
        "scripts/compress_and_archive.py",
        "scripts/compress_and_archive.py",
        "scripts/migrate_file_ids_to_s3.py",
        "scripts/populate_test_data.py",
        "scripts/test_subscriptions.py",
        "scripts/migrate_file_ids_to_s3.py",
        "migrations/env.py",
        "migrations/versions/711c8b8f6276_baseline_schema.py",
        ".github/workflows/ci.yml",
        "storage/s3.py",
        "storage/__init__.py",
        "tests/test_audit_log.py",
        "tests/test_cascade_relations.py",
        "tests/utils.py",
        "tests/smoke/test_billing_flow.py",
        "tests/smoke/test_core_flow.py",
        "tests/smoke/test_files_flow.py",
        "__init__.py",
        "database.py",
        "docker-compose.yml",
        "Makefile",
        "Dockerfile",
        "requirements.txt",
        "requirements-lint.txt",
        "requirements-dev.txt",
        "conftest.py",
        "pytest.ini",
        "check_connection.py",
        "worker.py",
        "alembic.ini",
        "config.py",
    ]

    output_file_name = "full_project_code.txt"

    print(
        "Начинаю сборку кода из указанных путей в файл '{}'...".format(output_file_name)
    )
    collect_code(files_to_collect, output_file_name)
    print("Готово! Код сохранен.")
