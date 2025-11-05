#!/usr/bin/env python3
"""
Manjaro System Maintenance GUI
A simple and secure GUI tool for updating and cleaning Manjaro Linux.
No AUR support — only official repositories.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import getpass


class ManjaroUpdater:
    ASKPASS = "/usr/bin/ssh-askpass"

    def __init__(self, root):
        self.root = root
        self.root.title("Менеджер системы Manjaro")
        self.root.minsize(800, 600)
        self.root.resizable(True, True)

        # Запрет запуска от root
        if getpass.getuser() == "root":
            messagebox.showerror(
                "Ошибка", 
                "❌ Не запускайте это приложение от root!\n"
                "Запускайте от обычного пользователя."
            )
            root.quit()
            return

        self._create_widgets()
        self.process = None
        self.running = False

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title = ttk.Label(main_frame, text="Менеджер системы Manjaro", font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 16))

        # Автообновление
        self.auto_btn = ttk.Button(
            main_frame,
            text="Автообновление и очистка (зеркала → система → кэш)",
            command=self.auto_full_maintenance
        )
        self.auto_btn.grid(row=1, column=0, columnspan=3, pady=(0, 12), sticky=(tk.W, tk.E))

        # Прогресс
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 12))

        # Колонки
        self._create_column(main_frame, 0, "Обновление системы", [
            ("Обновить зеркала", self.update_mirrors),
            ("Полное обновление системы", self.full_update)
        ])

        self._create_column(main_frame, 1, "Поддержка системы", [
            ("Проверить зависимости", self.check_dependencies),
            ("Исправить зависимости", self.fix_dependencies),
            ("Очистить кэш пакетов", self.clean_packages)
        ])

        self._create_column(main_frame, 2, "Очистка системы", [
            ("Удалить остаточные пакеты", self.clean_orphans),
            ("Очистить логи", self.clean_logs),
            ("Полная очистка системы", self.full_clean)
        ])

        # Стоп-кнопка
        self.stop_btn = ttk.Button(
            main_frame,
            text="Остановить текущую операцию",
            command=self.stop_process,
            state=tk.DISABLED
        )
        self.stop_btn.grid(row=4, column=0, columnspan=3, pady=(12, 12), sticky=(tk.W, tk.E))

        # Вывод
        self.output_text = scrolledtext.ScrolledText(main_frame, height=20, wrap=tk.WORD)
        self.output_text.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Статус
        self.status_label = ttk.Label(main_frame, text="Готово", foreground="blue")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=(12, 0))

        # Вес для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        for i in range(3):
            main_frame.columnconfigure(i, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def _create_column(self, parent, col, title, buttons):
        frame = ttk.LabelFrame(parent, text=title, padding="6")
        frame.grid(row=3, column=col, padx=(0 if col == 0 else 6, 0 if col == 2 else 6), sticky=(tk.N, tk.W, tk.E))
        for text, cmd in buttons:
            btn = ttk.Button(frame, text=text, command=cmd, width=24)
            btn.pack(pady=3)

    def append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, text, color="blue"):
        self.status_label.config(text=text, foreground=color)

    def run_command(self, command, description):
        try:
            self.append_output(f"\n--- {description} ---\n")
            self.update_status(f"Выполняется: {description}", "orange")

            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                preexec_fn=os.setsid
            )

            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    self.append_output(output)

            rc = self.process.poll()
            if rc == 0:
                self.append_output(f"\n✓ {description} успешно завершено!\n")
                self.update_status(f"✓ {description} завершено", "green")
            else:
                self.append_output(f"\n✗ {description} завершилось с ошибкой (код {rc})\n")
                self.update_status(f"✗ Ошибка: {description}", "red")
            return rc == 0
        except Exception as e:
            self.append_output(f"\n✗ Исключение: {e}\n")
            self.update_status("✗ Критическая ошибка", "red")
            return False

    def start_progress(self):
        self.progress.start(10)
        self.running = True
        self._set_buttons_state(tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.auto_btn.config(state=tk.DISABLED)

    def stop_progress(self):
        self.progress.stop()
        self.running = False
        self._set_buttons_state(tk.NORMAL)
        self.update_status("Готово")

    def _set_buttons_state(self, state):
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    if child not in (self.stop_btn, self.auto_btn):
                        child.config(state=state)
                elif isinstance(child, (ttk.Frame, ttk.LabelFrame)):
                    walk(child)
        walk(self.root)

    # ===============
    # Основные функции
    # ===============

    def _sudo_cmd(self, cmd):
        return f"env SUDO_ASKPASS={self.ASKPASS} sudo -A sh -c {cmd!r}"

    def update_mirrors(self):
        threading.Thread(target=self._run_task, args=(
            self._sudo_cmd("pacman-mirrors --fasttrack 5 && pacman -Syy"),
            "Обновление зеркал"
        ), daemon=True).start()

    def full_update(self):
        threading.Thread(target=self._run_task, args=(
            self._sudo_cmd("pacman -Syu --noconfirm"),
            "Полное обновление системы"
        ), daemon=True).start()

    def check_dependencies(self):
        threading.Thread(target=self._check_deps_task, daemon=True).start()

    def fix_dependencies(self):
        threading.Thread(target=self._fix_deps_task, daemon=True).start()

    def clean_packages(self):
        threading.Thread(target=self._run_task, args=(
            self._sudo_cmd("pacman -Sc --noconfirm"),
            "Очистка кэша пакетов"
        ), daemon=True).start()

    def clean_orphans(self):
        threading.Thread(target=self._clean_orphans_task, daemon=True).start()

    def clean_logs(self):
        threading.Thread(target=self._run_task, args=(
            self._sudo_cmd('journalctl --vacuum-time=7d && find /var/log -type f -name "*.log.*" -delete 2>/dev/null || true'),
            "Очистка логов"
        ), daemon=True).start()

    def full_clean(self):
        threading.Thread(target=self._full_clean_task, daemon=True).start()

    def auto_full_maintenance(self):
        threading.Thread(target=self._auto_maintenance_task, daemon=True).start()

    # ===============
    # Внутренние задачи
    # ===============

    def _run_task(self, cmd, desc):
        self.start_progress()
        try:
            if self.running and self.run_command(cmd, desc):
                self.append_output(f"\n✓ {desc} завершено.\n")
        finally:
            self.stop_progress()

    def _get_orphans(self):
        res = subprocess.run(
            "pacman -Qtdq",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )
        return res.stdout.strip()

    def _check_deps_task(self):
        self.start_progress()
        try:
            res = subprocess.run(
                "pacman -Qk 2>&1 | grep -E 'missing|changed|corrupted'",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            broken = res.stdout.strip()
            if broken:
                self.append_output(f"\n--- Проблемы ---\n{broken}\n")
                self.update_status("✗ Обнаружены повреждённые пакеты", "red")
            else:
                self.append_output("\n✓ Проблем не обнаружено.\n")
                self.update_status("✓ Проверка пройдена", "green")
        finally:
            self.stop_progress()

    def _fix_deps_task(self):
        self.start_progress()
        try:
            res = subprocess.run(
                "pacman -Qk 2>&1 | grep -E 'missing|changed|corrupted'",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            if not res.stdout.strip():
                self.append_output("\n✓ Проблем не обнаружено.\n")
                self.update_status("✓ Исправление не требуется", "green")
                return

            if not messagebox.askyesno("Подтверждение", "Обнаружены повреждённые пакеты. Обновить систему для исправления?"):
                return

            if not self.run_command(self._sudo_cmd("pacman -Syu --noconfirm"), "Обновление системы"):
                return

            orphans = self._get_orphans()
            if orphans and messagebox.askyesno("Остаточные пакеты", f"Найдено {len(orphans.splitlines())} остаточных пакетов. Удалить?"):
                self.run_command(self._sudo_cmd(f"pacman -Rns {orphans} --noconfirm"), "Удаление остаточных пакетов")

            self.append_output("\n✓ Исправление завершено.\n")
            self.update_status("✓ Исправление завершено", "green")
        finally:
            self.stop_progress()

    def _clean_orphans_task(self):
        self.start_progress()
        try:
            orphans = self._get_orphans()
            if not orphans:
                self.append_output("\n✓ Остаточных пакетов нет.\n")
                self.update_status("✓ Нет остаточных пакетов", "green")
                return
            if messagebox.askyesno("Подтверждение", f"Удалить остаточные пакеты?\n\n{orphans}"):
                self.run_command(self._sudo_cmd(f"pacman -Rns {orphans} --noconfirm"), "Удаление остаточных пакетов")
        finally:
            self.stop_progress()

    def _full_clean_task(self):
        self.start_progress()
        try:
            if not messagebox.askyesno("Подтверждение", "Выполнить полную очистку?\n• Кэш\n• Остаточные пакеты\n• Логи"):
                return

            orphans = self._get_orphans()
            cmd = "pacman -Sc --noconfirm"
            if orphans:
                cmd += f" && pacman -Rns {orphans} --noconfirm"
            self.run_command(self._sudo_cmd(cmd), "Очистка кэша и остаточных пакетов")
            self.run_command(self._sudo_cmd("journalctl --vacuum-time=7d"), "Очистка логов")
            self.append_output("\n✓ Полная очистка завершена!\n")
            self.update_status("✓ Полная очистка завершена", "green")
        finally:
            self.stop_progress()

    def _auto_maintenance_task(self):
        self.start_progress()
        try:
            if not messagebox.askyesno("Подтверждение", "Выполнить:\n1. Обновление зеркал\n2. Обновление системы\n3. Очистка кэша"):
                return

            # Единый вызов — один пароль
            cmd = (
                "pacman-mirrors --fasttrack 5 && "
                "pacman -Syy && "
                "pacman -Syu --noconfirm && "
                "pacman -Sc --noconfirm"
            )
            if self.running and self.run_command(self._sudo_cmd(cmd), "Автообновление и очистка"):
                self.append_output("\n🎉 Обслуживание завершено!\n")
                self.update_status("✅ Готово", "green")
            else:
                self.append_output("\n⚠ Автообновление прервано.\n")
        finally:
            self.stop_progress()

    def stop_process(self):
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), 15)  # SIGTERM
                self.append_output("\n⚠ Операция остановлена пользователем.\n")
                self.update_status("⚠ Остановлено", "red")
            except Exception as e:
                self.append_output(f"\n⚠ Не удалось остановить процесс: {e}\n")
        self.running = False
        self.stop_progress()


def main():
    try:
        root = tk.Tk()
        root.withdraw()  # Скрываем на время

        # Задаём желаемый размер
        width, height = 920, 760

        # Определяем геометрию ОСНОВНОГО монитора (тот, что содержит (0,0))
        temp = tk.Toplevel(root)
        temp.geometry("1x1+0+0")
        temp.update_idletasks()
        primary_width = temp.winfo_screenwidth()
        primary_height = temp.winfo_screenheight()
        temp.destroy()

        # Центрируем на основном мониторе
        x = (primary_width - width) // 2
        y = max(0, (primary_height - height) // 2)

        # Применяем геометрию и показываем
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.deiconify()  # Показываем окно

        app = ManjaroUpdater(root)
        root.mainloop()
    except Exception as e:
        import sys
        print(f"Критическая ошибка: {e}", file=sys.stderr)
        print("Убедитесь, что установлен пакет 'tk': sudo pacman -S tk", file=sys.stderr)


if __name__ == "__main__":
    import sys
    main()
