import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from __backup import DifferentialBackup
import datetime
from git import Repo

def remove_tree(path: Path):
    """
    アクセス拒否エラー対策のため、削除時にパーミッションを変更して再試行するユーティリティ関数。
    """
    def onerror(func, path, exc_info):
        os.chmod(path, 0o777)
        func(path)
    shutil.rmtree(path, onerror=onerror)

class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title('TRYBAI_CRAFTコマンド管理')

        # 各ディレクトリ設定
        self.command_path = Path("plugins/baisound")
        # バックアップは plugins/baisound_master/backup 以下に保存
        self.backup_path = Path("plugins/baisound_master/backup")
        # baseline（フルバックアップ）は "baseline_backup" という名称に変更
        self.baseline_folder = self.backup_path / "baseline_backup"
        # GitHubからクローンする先は従来の master_folder とする
        self.master_folder = self.backup_path / "master_folder"

        # DifferentialBackup の初期化
        # baseline_folder は "baseline_backup"、差分バックアップの接頭辞は "command_backup"
        self.backup_manager = DifferentialBackup(
            self.command_path,
            self.backup_path / "command_backup",
            baseline_folder=self.baseline_folder.name,
            diff_prefix="command_backup"
        )

        # バックアップ一覧の読み込み（差分バックアップは "command_backup_YYYYMMDDHHMMSS" 形式）
        self.backup_map = {}  # {表示用日時: 実際のフォルダ名}
        self.backups = self.load_backups()

        # GUI変数
        self.var_backup = tk.StringVar()

        # スタイル設定
        style = ttk.Style()
        style.configure('TFrame', background='white')
        style.configure('TLabel', background='white', font=('Yu Gothic UI', 9))
        style.configure('TButton', font=('Yu Gothic UI', 9))

        # メインフレーム
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Row 0: コマンドアップデートボタン
        update_button = ttk.Button(main_frame, text='コマンドアップデート', command=self.update_command)
        update_button.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Row 1: バックアップ選択用の Combobox（復元用）
        self.create_combobox(main_frame, '復元するバックアップを選択', self.var_backup, 1, self.backups)

        # Row 2: 復元ボタンと終了ボタン（ボタンフレーム）
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        restore_button = ttk.Button(button_frame, text='アップデート前に戻す', command=self.restore_previous_command)
        restore_button.grid(row=0, column=0, padx=5)
        exit_button = ttk.Button(button_frame, text='終了', command=root.quit)
        exit_button.grid(row=0, column=1, padx=5)

    def update_command(self) -> None:
        """
        GitHub からコマンドをダウンロードし、baisound フォルダに更新する。
        更新前に、既存の baisound.admin.properties を退避し、
        更新後にその内容で上書きすることで、ファイルが上書きされないようにします。
        また、クローン後に .git フォルダを削除します。
        """
        command_repo = "https://github.com/baisound/baisound-command.git"

        # 退避: 現在のコマンドフォルダ内の baisound.admin.properties の内容を保存
        old_admin_data = None
        admin_file_path = self.command_path / "baisound.admin.properties"
        if admin_file_path.exists():
            with open(admin_file_path, "rb") as f:
                old_admin_data = f.read()

        # 差分バックアップの作成（アップデート前の状態を保存）
        self.backup_manager.backup()

        try:
            # GitHubからクローンする前に、baseline_backup の更新は不要なのでそのままにする
            # master_folder を削除（アクセス拒否対策）
            if self.master_folder.exists():
                remove_tree(self.master_folder)
            self.master_folder.mkdir(parents=True, exist_ok=True)

            # GitHub から master_folder にクローン
            Repo.clone_from(command_repo, self.master_folder.as_posix())

            # .git フォルダが存在する場合は削除
            git_folder = self.master_folder / ".git"
            if git_folder.exists():
                remove_tree(git_folder)

            # 現在のコマンドフォルダを削除して更新
            if self.command_path.exists():
                remove_tree(self.command_path)
            shutil.copytree(self.master_folder, self.command_path)

            # 更新後、もし旧バージョンの admin.properties が存在していたら復元
            if old_admin_data is not None:
                with open(self.command_path / "baisound.admin.properties", "wb") as f:
                    f.write(old_admin_data)

            messagebox.showinfo('成功', 'コマンドがアップデートされました')
        except Exception as e:
            messagebox.showerror('エラー', f'コマンドアップデート中にエラーが発生しました:\n{str(e)}')

    def load_backups(self) -> list:
        """
        command_backup フォルダ内の差分バックアップフォルダ一覧を取得し、
        YYYY/MM/DD hh:mm:ss 形式で表示用リストを作成する。
        """
        backups = []
        backup_root = self.backup_path / "command_backup"
        if backup_root.exists():
            try:
                for d in sorted(backup_root.iterdir(), reverse=True):
                    if d.is_dir() and d.name.startswith("command_backup_"):
                        formatted_name = self.format_backup_name(d.name)
                        if formatted_name:
                            self.backup_map[formatted_name] = d.name
                            backups.append(formatted_name)
            except Exception as e:
                messagebox.showerror('エラー', f'バックアップの読み込み中にエラーが発生しました:\n{str(e)}')
        return backups

    def format_backup_name(self, folder_name: str) -> str:
        """
        フォルダ名 "command_backup_YYYYMMDDHHMMSS" を "YYYY/MM/DD hh:mm:ss" の形式に変換する。
        """
        prefix = "command_backup_"
        if folder_name.startswith(prefix):
            try:
                timestamp_str = folder_name[len(prefix):]
                dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                return dt.strftime("%Y/%m/%d %H:%M:%S")
            except ValueError:
                pass
        return None

    def create_combobox(self, parent, label_text, var, row, values: list):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        combobox = ttk.Combobox(parent, width=40, values=values, state="readonly", textvariable=var)
        combobox.grid(row=row, column=1, sticky=tk.W, pady=2)
        if values:
            combobox.current(0)

    def restore_previous_command(self):
        """
        コンボボックスで選択されたバックアップを元に、直前の状態にコマンドを復元する。
        """
        selected_display_name = self.var_backup.get()
        if not selected_display_name:
            messagebox.showwarning('警告', 'バックアップを選択してください')
            return

        selected_backup = self.backup_map.get(selected_display_name)
        if not selected_backup:
            messagebox.showerror('エラー', '選択したバックアップが見つかりません')
            return

        try:
            self.backup_manager.restore(selected_backup)
            messagebox.showinfo('成功', 'コマンドが直前の状態に復元されました')
            # 復元後、バックアップ一覧を更新
            self.backup_map.clear()
            self.backups = self.load_backups()
        except Exception as e:
            messagebox.showerror('エラー', f'復元中にエラーが発生しました:\n{str(e)}')


def main():
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
