#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os

class ManjaroUpdater:
    def __init__(self, root):
        self.root = root
        self.root.title("Менеджер системы Manjaro")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # Создаем основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Менеджер системы Manjaro", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Прогресс бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Кнопки - первая колонка
        col1_frame = ttk.LabelFrame(main_frame, text="Обновление системы", padding="5")
        col1_frame.grid(row=2, column=0, padx=(0, 5), sticky=(tk.N, tk.W, tk.E))
        self.mirror_btn = ttk.Button(col1_frame, text="Обновить зеркала", 
                                    command=self.update_mirrors, width=20)
        self.mirror_btn.pack(pady=2)
        self.update_btn = ttk.Button(col1_frame, text="Полное обновление системы", 
                                    command=self.full_update, width=20)
        self.update_btn.pack(pady=2)
        self.yay_update_btn = ttk.Button(col1_frame, text="Обновить пакеты AUR", 
                                        command=self.yay_update, width=20)
        self.yay_update_btn.pack(pady=2)
        
        # Кнопки - вторая колонка
        col2_frame = ttk.LabelFrame(main_frame, text="Поддержка системы", padding="5")
        col2_frame.grid(row=2, column=1, padx=(5, 5), sticky=(tk.N, tk.W, tk.E))
        self.check_deps_btn = ttk.Button(col2_frame, text="Проверить зависимости", 
                                        command=self.check_dependencies, width=20)
        self.check_deps_btn.pack(pady=2)
        self.fix_deps_btn = ttk.Button(col2_frame, text="Исправить зависимости", 
                                      command=self.fix_dependencies, width=20)
        self.fix_deps_btn.pack(pady=2)
        self.clean_btn = ttk.Button(col2_frame, text="Очистить кэш пакетов", 
                                   command=self.clean_packages, width=20)
        self.clean_btn.pack(pady=2)
        
        # Кнопки - третья колонка
        col3_frame = ttk.LabelFrame(main_frame, text="Очистка системы", padding="5")
        col3_frame.grid(row=2, column=2, padx=(5, 0), sticky=(tk.N, tk.W, tk.E))
        self.clean_orphans_btn = ttk.Button(col3_frame, text="Удалить остаточные пакеты", 
                                           command=self.clean_orphans, width=20)
        self.clean_orphans_btn.pack(pady=2)
        self.clean_logs_btn = ttk.Button(col3_frame, text="Очистить логи", 
                                        command=self.clean_logs, width=20)
        self.clean_logs_btn.pack(pady=2)
        self.full_clean_btn = ttk.Button(col3_frame, text="Полная очистка системы", 
                                        command=self.full_clean, width=20)
        self.full_clean_btn.pack(pady=2)
        
        # Стоп кнопка
        self.stop_btn = ttk.Button(main_frame, text="Остановить текущую операцию", 
                                  command=self.stop_process, state=tk.DISABLED)
        self.stop_btn.grid(row=3, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        
        # Текстовое поле для вывода
        self.output_text = scrolledtext.ScrolledText(main_frame, height=20, width=100)
        self.output_text.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Статусная строка
        self.status_label = ttk.Label(main_frame, text="Готово", foreground="blue")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        # Настройка растягивания
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        self.process = None
        self.running = False

    def append_output(self, text):
        """Добавить текст в окно вывода"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, text, color="blue"):
        """Обновить статусную строку"""
        self.status_label.config(text=text, foreground=color)

    def run_command(self, command, description):
        """Запустить команду и показать вывод"""
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
            
            return_code = self.process.poll()
            if return_code == 0:
                self.append_output(f"\n✓ {description} успешно завершено!\n")
                self.update_status(f"✓ {description} завершено", "green")
            else:
                self.append_output(f"\n✗ {description} завершилось с ошибкой кода {return_code}\n")
                self.update_status(f"✗ {description} не удалось", "red")
            return return_code == 0
        except Exception as e:
            self.append_output(f"\n✗ Ошибка при выполнении {description}: {str(e)}\n")
            self.update_status(f"✗ Ошибка: {str(e)}", "red")
            return False

    def start_progress(self):
        """Запустить прогресс бар"""
        self.progress.start(10)
        self.running = True
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, ttk.Frame)):
                        if hasattr(child, 'winfo_children'):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, ttk.Button) and subchild != self.stop_btn:
                                    subchild.config(state=tk.DISABLED)
                        elif isinstance(child, ttk.Button) and child != self.stop_btn:
                            child.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_progress(self):
        """Остановить прогресс бар"""
        self.progress.stop()
        self.running = False
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, ttk.Frame)):
                        if hasattr(child, 'winfo_children'):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, ttk.Button):
                                    subchild.config(state=tk.NORMAL)
                        elif isinstance(child, ttk.Button):
                            child.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("Готово")

    def update_mirrors(self):
        """Обновить зеркала"""
        def run():
            self.start_progress()
            try:
                commands = [
                    ("sudo pacman-mirrors --fasttrack 5 && sudo pacman -Syy", "Обновление быстрых зеркал"),
                ]
                success = True
                for command, description in commands:
                    if not self.running:
                        break
                    if not self.run_command(command, description):
                        success = False
                        break
                if success and self.running:
                    self.append_output("\n✓ Обновление зеркал успешно завершено!\n")
                    self.update_status("✓ Обновление зеркал завершено", "green")
                elif not self.running:
                    self.append_output("\n⚠ Обновление зеркал отменено\n")
                    self.update_status("⚠ Отменено", "orange")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def full_update(self):
        """Полное обновление системы"""
        def run():
            self.start_progress()
            try:
                commands = [
                    ("sudo pacman -Syu --noconfirm", "Полное обновление системы"),
                ]
                success = True
                for command, description in commands:
                    if not self.running:
                        break
                    if not self.run_command(command, description):
                        success = False
                        break
                if success and self.running:
                    self.append_output("\n✓ Полное обновление системы успешно завершено!\n")
                    self.update_status("✓ Полное обновление завершено", "green")
                elif not self.running:
                    self.append_output("\n⚠ Полное обновление отменено\n")
                    self.update_status("⚠ Отменено", "orange")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def yay_update(self):
        """Обновление через yay"""
        def run():
            self.start_progress()
            try:
                commands = [
                    ("yay -Syu --noconfirm", "Обновление пакетов AUR"),
                ]
                success = True
                for command, description in commands:
                    if not self.running:
                        break
                    if not self.run_command(command, description):
                        success = False
                        break
                if success and self.running:
                    self.append_output("\n✓ Обновление пакетов AUR успешно завершено!\n")
                    self.update_status("✓ Обновление AUR завершено", "green")
                elif not self.running:
                    self.append_output("\n⚠ Обновление AUR отменено\n")
                    self.update_status("⚠ Отменено", "orange")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def check_dependencies(self):
        """Проверка зависимостей"""
        def run():
            self.start_progress()
            try:
                self.append_output("\n--- Проверка целостности пакетов ---\n")
                check_cmd = "pacman -Qk 2>&1 | grep -E 'missing|changed|corrupted'"
                result = subprocess.run(
                    check_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                broken = result.stdout.strip()
                if broken:
                    self.append_output(f"Обнаружены проблемы:\n{broken}\n")
                    self.update_status("✗ Обнаружены проблемы с пакетами", "red")
                else:
                    self.append_output("✓ Нет проблем с целостностью пакетов.\n")
                    self.update_status("✓ Проверка зависимостей: всё в порядке", "green")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def fix_dependencies(self):
        """Проверка и исправление реальных проблем с зависимостями"""
        def run():
            self.start_progress()
            try:
                self.append_output("\n--- Поиск проблем с пакетами ---\n")
                
                # Проверяем только реально сломанные файлы
                check_cmd = "pacman -Qk 2>&1 | grep -E 'missing|changed|corrupted'"
                result = subprocess.run(
                    check_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                broken_output = result.stdout.strip()

                if not broken_output:
                    self.append_output("✓ Нет проблем с пакетами — исправление не требуется.\n")
                    self.update_status("✓ Нет проблем с зависимостями", "green")
                    self.stop_progress()
                    return

                self.append_output(f"Обнаружены проблемы:\n{broken_output}\n")
                if not messagebox.askyesno("Подтверждение", "Обнаружены проблемы с пакетами. Выполнить обновление системы для исправления?"):
                    self.append_output("⚠ Исправление отменено пользователем.\n")
                    self.update_status("⚠ Отменено пользователем", "orange")
                    self.stop_progress()
                    return

                # Шаг 1: Обновление системы
                if not self.run_command("sudo pacman -Syu --noconfirm", "Обновление системы"):
                    self.append_output("✗ Не удалось обновить систему.\n")
                    self.update_status("✗ Обновление не удалось", "red")
                    self.stop_progress()
                    return

                # Шаг 2: Повторная проверка
                self.append_output("\n--- Повторная проверка после обновления ---\n")
                result_after = subprocess.run(
                    check_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                if result_after.stdout.strip():
                    self.append_output("⚠ Некоторые проблемы остались. Рекомендуется ручное вмешательство.\n")
                    self.update_status("⚠ Остались проблемы", "red")
                else:
                    self.append_output("✓ Все проблемы с пакетами исправлены.\n")
                    self.update_status("✓ Зависимости исправлены", "green")

                # Шаг 3: Удаление остаточных пакетов (по желанию)
                orphan_check = "pacman -Qtdq"
                orphan_result = subprocess.run(
                    orphan_check,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    universal_newlines=True
                )
                orphans = orphan_result.stdout.strip()
                if orphans:
                    if messagebox.askyesno("Остаточные пакеты", f"Найдено {len(orphans.splitlines())} остаточных пакетов. Удалить?"):
                        self.run_command(f"sudo pacman -Rns {orphans} --noconfirm", "Удаление остаточных пакетов")
                    else:
                        self.append_output("✓ Остаточные пакеты не удалены.\n")
                else:
                    self.append_output("✓ Остаточных пакетов не найдено.\n")

                self.append_output("\n✓ Проверка и исправление завершены.\n")

            except Exception as e:
                self.append_output(f"\n✗ Ошибка: {str(e)}\n")
                self.update_status(f"✗ Ошибка: {str(e)}", "red")
            finally:
                self.stop_progress()

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def clean_packages(self):
        """Очистка кэша пакетов"""
        def run():
            self.start_progress()
            try:
                commands = [
                    ("sudo pacman -Sc --noconfirm", "Очистка кэша пакетов (сохранить последние версии)"),
                    ("yay -Sc --noconfirm", "Очистка кэша yay"),
                ]
                success = True
                for command, description in commands:
                    if not self.running:
                        break
                    if not self.run_command(command, description):
                        success = False
                        break
                if success and self.running:
                    self.append_output("\n✓ Очистка кэша пакетов завершена!\n")
                    self.update_status("✓ Очистка кэша завершена", "green")
                elif not self.running:
                    self.append_output("\n⚠ Очистка кэша отменена\n")
                    self.update_status("⚠ Отменено", "orange")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def clean_orphans(self):
        """Удаление остаточных пакетов"""
        def run():
            self.start_progress()
            try:
                orphan_check = "pacman -Qtdq"
                orphan_result = subprocess.run(
                    orphan_check,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    universal_newlines=True
                )
                orphans = orphan_result.stdout.strip()
                if not orphans:
                    self.append_output("\n✓ Остаточных пакетов не найдено.\n")
                    self.update_status("✓ Нет остаточных пакетов", "green")
                    self.stop_progress()
                    return

                if messagebox.askyesno("Подтверждение", f"Удалить следующие остаточные пакеты?\n\n{orphans}"):
                    command = f"sudo pacman -Rns {orphans} --noconfirm"
                    self.run_command(command, "Удаление остаточных пакетов")
                else:
                    self.append_output("\n⚠ Удаление остаточных пакетов отменено пользователем.\n")
                    self.update_status("⚠ Отменено", "orange")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def clean_logs(self):
        """Очистка логов"""
        def run():
            self.start_progress()
            try:
                commands = [
                    ("sudo journalctl --vacuum-time=7d", "Очистка журналов systemd (сохранить 7 дней)"),
                    ("sudo rm -f /var/log/*.log.* 2>/dev/null || true", "Удаление старых файлов логов"),
                ]
                success = True
                for command, description in commands:
                    if not self.running:
                        break
                    if not self.run_command(command, description):
                        success = False
                        break
                if success and self.running:
                    self.append_output("\n✓ Очистка логов завершена!\n")
                    self.update_status("✓ Очистка логов завершена", "green")
                elif not self.running:
                    self.append_output("\n⚠ Очистка логов отменена\n")
                    self.update_status("⚠ Отменено", "orange")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def full_clean(self):
        """Полная очистка системы"""
        def run():
            self.start_progress()
            try:
                if not messagebox.askyesno("Подтверждение", "Выполнить полную очистку системы?\nБудет очищен кэш, логи и удалены остаточные пакеты."):
                    self.append_output("\n⚠ Полная очистка отменена пользователем.\n")
                    self.update_status("⚠ Отменено", "orange")
                    self.stop_progress()
                    return

                self.append_output("\n=== ПОЛНАЯ ОЧИСТКА СИСТЕМЫ ===\n")
                commands = [
                    ("sudo pacman -Sc --noconfirm", "Очистка кэша пакетов"),
                    ("sudo pacman -Rns $(pacman -Qtdq) --noconfirm 2>/dev/null || true", "Удаление остаточных пакетов"),
                    ("yay -Sc --noconfirm", "Очистка кэша yay"),
                    ("sudo journalctl --vacuum-time=7d", "Очистка systemd журналов"),
                ]
                success = True
                for command, description in commands:
                    if not self.running:
                        break
                    if not self.run_command(command, description):
                        success = False
                        break
                if success and self.running:
                    self.append_output("\n✓ Полная очистка системы завершена!\n")
                    self.update_status("✓ Полная очистка завершена", "green")
                elif not self.running:
                    self.append_output("\n⚠ Полная очистка отменена\n")
                    self.update_status("⚠ Отменено", "orange")
            finally:
                self.stop_progress()
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def stop_process(self):
        """Остановить текущий процесс"""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), 15)  # SIGTERM
                self.append_output("\n⚠ Процесс остановлен пользователем\n")
                self.update_status("⚠ Остановлено пользователем", "red")
            except Exception as e:
                self.append_output(f"\n⚠ Не удалось остановить процесс: {e}\n")
        self.running = False
        self.stop_progress()


def main():
    try:
        root = tk.Tk()
        app = ManjaroUpdater(root)
        # Центрирование окна
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        root.mainloop()
    except Exception as e:
        print(f"Ошибка запуска GUI: {e}")
        print("Убедитесь, что tkinter установлен:")
        print("sudo pacman -S tk")


if __name__ == "__main__":
    main()
