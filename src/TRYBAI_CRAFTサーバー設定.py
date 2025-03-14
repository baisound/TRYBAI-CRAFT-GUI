import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from __backup import DifferentialBackup

# 初期設定のデフォルト値（全て文字列）
DEFAULT_CONFIG = {
    "allow-flight": "false",
    "allow-nether": "true",
    "broadcast-console-to-ops": "true",
    "broadcast-rcon-to-ops": "true",
    "debug": "false",
    "difficulty": "easy",
    "enable-command-block": "false",
    "enable-jmx-monitoring": "false",
    "enable-query": "false",
    "enable-rcon": "false",
    "enable-status": "true",
    "enforce-secure-profile": "true",
    "enforce-whitelist": "false",
    "entity-broadcast-range-percentage": "100",
    "force-gamemode": "false",
    "function-permission-level": "2",
    "gamemode": "survival",
    "generate-structures": "true",
    "generator-settings": "",
    "hardcore": "false",
    "hide-online-players": "false",
    "initial-disabled-packs": "",
    "initial-enabled-packs": "vanilla",
    "level-name": "サバイバル",
    "level-seed": "",
    "level-type": "default",
    "max-chained-neighbor-updates": "1000000",
    "max-players": "20",
    "max-tick-time": "60000",
    "max-world-size": "29999984",
    "motd": "A Minecraft Server",
    "network-compression-threshold": "256",
    "online-mode": "true",
    "op-permission-level": "4",
    "player-idle-timeout": "0",
    "prevent-proxy-connections": "false",
    "pvp": "true",
    "query.port": "25565",
    "rate-limit": "0",
    "rcon.password": "",
    "rcon.port": "25575",
    "require-resource-pack": "false",
    "resource-pack": "",
    "resource-pack-prompt": "",
    "resource-pack-sha1": "",
    "server-ip": "",
    "server-port": "25565",
    "simulation-distance": "10",
    "spawn-animals": "true",
    "spawn-monsters": "true",
    "spawn-npcs": "true",
    "spawn-protection": "16",
    "sync-chunk-writes": "true",
    "text-filtering-config": "",
    "use-native-transport": "true",
    "view-distance": "10",
    "white-list": "false"
}


def save_properties(path: Path, config: dict) -> None:
    """
    設定値を server.properties ファイルとして保存する。
    level-name は「配布ワールド\」の接頭辞を付与して保存する。
    """
    settings = config.copy()
    # level-name の値に「配布ワールド\」を付与（既に含まれていた場合は置換）
    level_name = settings.get("level-name", "")
    # 既に「配布ワールド\」が付いている場合は取り除く
    if level_name.startswith("配布ワールド\\"):
        level_name = level_name[len("配布ワールド\\"):]
    settings["level-name"] = f"配布ワールド\\{level_name}"

    # キー順にソートして書き出す
    lines = [f"{k}={v}" for k, v in sorted(settings.items())]
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))


class ConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title('TRYBAI_CRAFTサーバー設定')

        # 設定値を保持する辞書（ファイルから読み込みまたはデフォルトを利用）
        self.config = self.load_existing_settings()
        # Tkinterウィジェットと連動する変数群
        self.config_vars = {}

        # 配布ワールドディレクトリの内容（存在する場合）
        self.worlds = self.load_worlds()

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

        # 各入力ウィジェットの作成
        self.create_combobox(main_frame, 'ワールド選択', 'level-name', 0, self.worlds if self.worlds else ["サバイバル"])
        self.create_checkbox(main_frame, "飛行MODの許可", "allow-flight", 1)
        self.create_checkbox(main_frame, "ネザー有効化", "allow-nether", 2)
        self.create_combobox(main_frame, "難易度", "difficulty", 3, ["peaceful", "easy", "normal", "hard"])
        self.create_checkbox(main_frame, "ゲームモードの強制", "force-gamemode", 4)
        self.create_combobox(main_frame, "ゲームモード", "gamemode", 5, ["survival", "creative", "adventure", "spectator"])
        self.create_checkbox(main_frame, "ハードコアモード", "hardcore", 6)
        self.create_combobox(main_frame, "新規生成マップタイプ", "level-type", 7, ["default", "flat", "largeBiomes", "amplified", "buffet"])
        self.create_checkbox(main_frame, "PVP有効化", "pvp", 8)
        self.create_checkbox(main_frame, "モンスタースポーン", "spawn-monsters", 9)
        self.create_checkbox(main_frame, "村人スポーン", "spawn-npcs", 10)

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=11, column=0, columnspan=2, pady=10)

        save_button = ttk.Button(button_frame, text='設定を保存', command=self.save_settings)
        save_button.grid(row=0, column=0, padx=5)

        exit_button = ttk.Button(button_frame, text='終了', command=root.quit)
        exit_button.grid(row=0, column=1, padx=5)

    def load_existing_settings(self) -> dict:
        """
        server.properties から設定値を読み込み、辞書として返す。
        ファイルが存在しない場合は DEFAULT_CONFIG を返す。
        コメント行（#で始まる行）はスキップする。
        """
        property_path = Path('server.properties')
        config = DEFAULT_CONFIG.copy()
        if property_path.exists():
            try:
                with open(property_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            if key == "level-name":
                                # 接頭辞「配布ワールド\」を取り除く
                                if value.startswith("配布ワールド\\"):
                                    value = value[len("配布ワールド\\"):]
                            config[key] = value
            except Exception as e:
                messagebox.showerror('エラー', f'設定の読み込み中にエラーが発生しました:\n{str(e)}')
        return config

    def load_worlds(self) -> list:
        """
        配布ワールドディレクトリ内のフォルダ一覧を返す。
        存在しない場合は空リスト。
        """
        worlds_path = Path('配布ワールド')
        if worlds_path.exists():
            try:
                return [d for d in os.listdir(worlds_path) if os.path.isdir(worlds_path / d)]
            except Exception as e:
                messagebox.showerror('エラー', f'ワールドの読み込み中にエラーが発生しました:\n{str(e)}')
        return []

    def create_combobox(self, parent, label_text, key, row, values: list):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        var = tk.StringVar(value=self.config.get(key, values[0]))
        combobox = ttk.Combobox(parent, width=40, values=values, state="readonly", textvariable=var)
        combobox.grid(row=row, column=1, sticky=tk.W, pady=2)
        # もし現在の値がリストにない場合は先頭を選択
        if var.get() not in values:
            combobox.current(0)
        self.config_vars[key] = var

    def create_checkbox(self, parent, label_text, key, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        # 文字列 "true"/"false" を Boolean に変換して初期値にする
        initial = True if self.config.get(key, "false").lower() == "true" else False
        var = tk.BooleanVar(value=initial)
        checkbox = ttk.Checkbutton(parent, variable=var)
        checkbox.grid(row=row, column=1, sticky=tk.W, pady=2)
        self.config_vars[key] = var

    def save_settings(self):
        try:
            # 保存先のパス
            property_path = Path('server.properties')
            backup_path = Path("backup")
            worlds_path = Path("配布ワールド")

            # ディレクトリの作成（存在しない場合）
            backup_path.mkdir(parents=True, exist_ok=True)
            worlds_path.mkdir(parents=True, exist_ok=True)

            # バックアップ処理
            backup_obj = DifferentialBackup(worlds_path, backup_path)
            backup_obj.create_baseline()
            backup_obj.backup()

            # 各ウィジェットの値を収集（チェックボックスは boolean なので文字列に変換）
            new_config = {}
            for key, var in self.config_vars.items():
                if isinstance(var, tk.BooleanVar):
                    new_config[key] = "true" if var.get() else "false"
                else:
                    new_config[key] = var.get()
            # 他の設定項目は既存の値を維持（必要に応じて更新）
            for key in self.config:
                if key not in new_config:
                    new_config[key] = self.config[key]

            # 設定ファイルの保存
            save_properties(property_path, new_config)

            messagebox.showinfo('成功', '設定が保存されました')
        except Exception as e:
            messagebox.showerror('エラー', f'エラーが発生しました:\n{str(e)}')


def main():
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
