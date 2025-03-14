import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from __backup import DifferentialBackup
import datetime


class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title('TRYBAI_CRAFTワールド復元')

        # 各ディレクトリ設定
        self.backup_path = Path("backup")
        self.worlds_path = Path("配布ワールド")
        self.world_backup_path = self.backup_path / "world_backup"  # backupフォルダ内にworld_backupを格納

        # バックアップ一覧を取得（フォーマット済み）
        self.backup_map = {}  # {表示名: 実際のフォルダ名}
        self.backups = self.load_backups()

        # GUI変数
        self.var_backup = tk.StringVar()

        # スタイル設定
        style = ttk.Style()
        style.configure('TFrame', background='white')
        style.configure('TLabel', background='white', font=('Yu Gothic UI', 9))
        style.configure('TEntry', font=('Yu Gothic UI', 9))
        style.configure('TButton', font=('Yu Gothic UI', 9))
        style.configure('TCheckbutton', background='white', font=('Yu Gothic UI', 9))

        # メインフレーム
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # バックアップ選択用のCombobox
        self.create_combobox(main_frame, '復元するバックアップを選択', self.var_backup, 0, self.backups)

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        restore_button = ttk.Button(button_frame, text='ワールドを復元', command=self.restore_backup)
        restore_button.grid(row=0, column=0, padx=5)

        undo_button = ttk.Button(button_frame, text='直前の状態に戻す', command=self.restore_previous_world)
        undo_button.grid(row=0, column=1, padx=5)

        exit_button = ttk.Button(button_frame, text='終了', command=root.quit)
        exit_button.grid(row=0, column=2, padx=5)

    def load_backups(self) -> list:
        """
        backupフォルダ内の差分バックアップフォルダ一覧を取得し、
        YYYY/MM/DD hh:mm:ss 形式でフォーマットして表示用リストを作成する。
        """
        backups = []
        if self.backup_path.exists():
            try:
                for d in sorted(self.backup_path.iterdir(), reverse=True):
                    if d.is_dir() and not str(d).endswith("world_backup"):  # world_backupは除外
                        formatted_name = self.format_backup_name(d.name)
                        if formatted_name:
                            self.backup_map[formatted_name] = d.name
                            backups.append(formatted_name)
            except Exception as e:
                messagebox.showerror('エラー', f'バックアップの読み込み中にエラーが発生しました:\n{str(e)}')
        return backups

    def format_backup_name(self, folder_name: str) -> str:
        """
        フォルダ名 "diff_backup_YYYYMMDDHHMMSS" を "YYYY/MM/DD hh:mm:ss" の形式に変換する。
        """
        prefix = "diff_backup_"
        if folder_name.startswith(prefix):
            try:
                timestamp_str = folder_name[len(prefix):]
                dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                return dt.strftime("%Y/%m/%d %H:%M:%S")
            except ValueError:
                pass  # 無効なフォーマットの場合はスキップ
        return None

    def create_combobox(self, parent, label_text, var, row, values: list):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        combobox = ttk.Combobox(parent, width=40, values=values, state="readonly", textvariable=var)
        combobox.grid(row=row, column=1, sticky=tk.W, pady=2)
        if values:
            combobox.current(0)

    def backup_current_world(self):
        """
        現在のワールドを `backup/world_backup` にバックアップする。
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir = self.world_backup_path / f"world_backup_{timestamp}"

        # 退避フォルダの管理（最新5個を保持）
        self.world_backup_path.mkdir(parents=True, exist_ok=True)
        old_backups = sorted(self.world_backup_path.iterdir(), key=lambda d: d.stat().st_mtime)
        while len(old_backups) >= 5:
            shutil.rmtree(old_backups.pop(0))

        # ワールドフォルダをバックアップ
        if self.worlds_path.exists():
            shutil.copytree(self.worlds_path, backup_dir)
            print(f"現在のワールドを退避しました: {backup_dir}")

    def restore_backup(self):
        """
        選択されたバックアップを使用してワールドを復元する。
        """
        selected_display_name = self.var_backup.get()
        if not selected_display_name:
            messagebox.showwarning('警告', 'バックアップを選択してください')
            return

        # 表示用の日時を元のフォルダ名に変換
        selected_backup = self.backup_map.get(selected_display_name)
        if not selected_backup:
            messagebox.showerror('エラー', '選択したバックアップが見つかりません')
            return

        try:
            self.backup_current_world()  # 現在のワールドを退避
            backup_manager = DifferentialBackup(self.worlds_path, self.backup_path)
            backup_manager.restore(selected_backup)
            messagebox.showinfo('成功', f'ワールドが {selected_display_name} に復元されました')
        except Exception as e:
            messagebox.showerror('エラー', f'復元中にエラーが発生しました:\n{str(e)}')

    def restore_previous_world(self):
        """
        直前の状態にワールドを戻す（`backup/world_backup` から復元）。
        """
        old_backups = sorted(self.world_backup_path.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
        if not old_backups:
            messagebox.showwarning('警告', '直前のワールドバックアップがありません')
            return

        latest_backup = old_backups[0]  # 最新のバックアップを取得
        try:
            if self.worlds_path.exists():
                shutil.rmtree(self.worlds_path)
            shutil.copytree(latest_backup, self.worlds_path)
            messagebox.showinfo('成功', 'ワールドが直前の状態に復元されました')
        except Exception as e:
            messagebox.showerror('エラー', f'復元中にエラーが発生しました:\n{str(e)}')


def main():
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
