import os
import shutil
import filecmp
import datetime
from pathlib import Path

class DifferentialBackup:
    """
    差分バックアップおよび復元を行うクラスです。

    Attributes:
        source (Path): バックアップ対象のソースディレクトリ
        backup_root (Path): バックアップデータを格納するルートディレクトリ
        baseline_dir (Path): フルバックアップ（ベースライン）を格納するディレクトリ
        diff_dir_prefix (str): 差分バックアップディレクトリの接頭辞
    """

    def __init__(self, source: Path, backup_root: Path, baseline_folder: str = "full_backup", diff_prefix: str = "diff_backup"):
        self.source = source
        self.backup_root = backup_root
        self.baseline_dir = self.backup_root / baseline_folder
        self.diff_dir_prefix = diff_prefix

    def create_baseline(self) -> None:
        """
        ソースディレクトリのフルバックアップ（ベースライン）を作成します。
        既にベースラインが存在する場合は何もしません。
        """
        if not self.baseline_dir.exists():
            print(f"Creating baseline backup at: {self.baseline_dir}")
            shutil.copytree(self.source, self.baseline_dir)
        else:
            print("Baseline backup already exists.")

    def cleanup_old_backups(self) -> None:
        """
        差分バックアップディレクトリが5個以上存在する場合、古い方から削除して
        総数が9個になるようにします（新規バックアップ作成後に全体で10個となるように）。
        """
        # diff_backup_で始まるディレクトリ一覧を取得し、名前順（タイムスタンプ順）にソート
        diff_dirs = sorted(
            [d for d in self.backup_root.iterdir() if d.is_dir() and d.name.startswith(f"{self.diff_dir_prefix}_")]
        )
        while len(diff_dirs) >= 55:
            oldest = diff_dirs.pop(0)
            shutil.rmtree(oldest)
            print(f"Removed old differential backup: {oldest}")

    def backup(self) -> None:
        """
        ソースディレクトリとベースラインを比較し、変更または新規追加されたファイルのみを
        差分バックアップとして保存します。差分バックアップはタイムスタンプ付きのディレクトリに保存され、
        バックアップ数が10個以上になった場合、古いものから削除されます。
        """
        # まずベースラインの作成を確認
        self.create_baseline()

        # 古い差分バックアップを削除（10個以上ある場合）
        self.cleanup_old_backups()

        # タイムスタンプ付きの差分バックアップディレクトリを作成
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        diff_dir = self.backup_root / f"{self.diff_dir_prefix}_{timestamp}"
        diff_dir.mkdir(parents=True, exist_ok=True)

        # ソースディレクトリ内を走査し、ベースラインと比較
        for root, dirs, files in os.walk(self.source):
            for file in files:
                src_file = Path(root) / file
                rel_path = src_file.relative_to(self.source)
                baseline_file = self.baseline_dir / rel_path
                # ファイルが存在しないか、内容が異なる場合のみコピー
                if (not baseline_file.exists() or not filecmp.cmp(src_file, baseline_file, shallow=False)):
                    target_dir = diff_dir / rel_path.parent
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, target_dir / file)
        print(f"Differential backup completed at: {diff_dir}")

    def restore(self, diff_backup_folder: str) -> None:
        """
        ベースラインバックアップと指定した差分バックアップを組み合わせてソースディレクトリを復元します。
        復元前に既存のソースディレクトリは削除されます。

        Args:
            diff_backup_folder (str): 復元に使用する差分バックアップのフォルダ名（backup_root直下のフォルダ名）
        """
        diff_dir = self.backup_root / diff_backup_folder

        if not self.baseline_dir.exists():
            raise FileNotFoundError("Baseline backup not found. Cannot restore.")

        if not diff_dir.exists():
            raise FileNotFoundError(f"Differential backup folder '{diff_backup_folder}' not found.")

        # 現在のソースディレクトリを削除して、ベースラインバックアップをコピー
        if self.source.exists():
            shutil.rmtree(self.source)
        shutil.copytree(self.baseline_dir, self.source)

        # 差分バックアップのファイルをソースディレクトリに上書きコピー
        for root, dirs, files in os.walk(diff_dir):
            for file in files:
                diff_file = Path(root) / file
                rel_path = diff_file.relative_to(diff_dir)
                target_file = self.source / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(diff_file, target_file)
        print("Restore completed successfully.")

# 使用例
# if __name__ == "__main__":
#     # バックアップ対象のディレクトリとバックアップデータを保存するディレクトリを指定
#     source_directory = "path/to/source_directory"
#     backup_directory = "path/to/backup_directory"

#     backup_tool = DifferentialBackup(source=source_directory, backup_root=backup_directory)

#     # 差分バックアップの作成
#     backup_tool.backup()

#     # 復元例（例：直近で作成された差分バックアップフォルダ名を指定）
#     # diff_folder = "diff_backup_20250312120000"
#     # backup_tool.restore(diff_backup_folder=diff_folder)
