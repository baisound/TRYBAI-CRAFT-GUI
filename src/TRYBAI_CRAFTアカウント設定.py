from ruamel.yaml import YAML
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path

def save_properties(path, license_key, token):
    # 既存の設定を保持するための辞書
    settings = {
        'licenseKey': 'ライセンスの設定をしてください',
        'token': 'トークンの設定をしてください',
        'connectTimeout': '5000',
        'readTimeout': '5000',
        'apiEndpoint': 'http://52.195.57.50/api/v1/'
    }

    # 既存のファイルから設定を読み込む
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    settings[key] = value

    # 新しい設定を適用
    if license_key:
        settings['licenseKey'] = license_key
    if token:
        settings['token'] = token

    # 設定を保存
    content = '\n'.join(f'{k}={v}' for k, v in settings.items())
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

class ConfigApp:
    def __init__(self, root):
        self.yaml = YAML()
        # YAMLの出力設定を調整
        self.yaml.preserve_quotes = True
        self.yaml.explicit_start = False  # ドキュメント開始マーカーを無効化
        self.yaml.width = 4096  # 行の折り返しを防止
        # インデントの設定
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        # セミコロンを防ぐための設定
        self.yaml.default_flow_style = False
        self.yaml.allow_unicode = True
        self.root = root
        self.root.title('TRYBAI_CRAFTアカウント設定')

        self.entries = {}
        self.is_test = tk.BooleanVar()

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

        # 入力フィールド
        self.create_input_field(main_frame, 'License Key:', '-LICENSE-', 0, show='*')
        self.create_input_field(main_frame, 'Token:', '-TOKEN-', 1, show='*')
        self.create_input_field(main_frame, 'TikTok ID:', '-TIKTOK-ID-', 2)
        self.create_input_field(main_frame, 'Minecraft ID:', '-MINECRAFT-ID-', 3)

        # テストモードのチェックボックスとstreamer入力フィールド
        test_frame = ttk.Frame(main_frame)
        test_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.test_check = ttk.Checkbutton(test_frame,
                                        text='テストモード',
                                        variable=self.is_test,
                                        command=self.toggle_streamer)
        self.test_check.grid(row=0, column=0, padx=(0, 10))

        ttk.Label(test_frame, text='Streamer:').grid(row=0, column=1, padx=(0, 5))
        self.streamer_entry = ttk.Entry(test_frame, width=30, state='disabled')
        self.streamer_entry.grid(row=0, column=2)
        self.entries['-STREAMER-'] = self.streamer_entry

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        save_button = ttk.Button(button_frame, text='設定を保存', command=self.save_settings)
        save_button.grid(row=0, column=0, padx=5)

        exit_button = ttk.Button(button_frame, text='終了', command=root.quit)
        exit_button.grid(row=0, column=1, padx=5)

        self.load_existing_settings()

    def toggle_streamer(self):
        """テストモードのオン/オフでstreamer入力フィールドの状態を切り替える"""
        if self.is_test.get():
            self.streamer_entry.configure(state='normal')
        else:
            self.streamer_entry.delete(0, tk.END)
            self.streamer_entry.configure(state='disabled')

    def create_input_field(self, parent, label_text, key, row, show=''):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(parent, width=40, show=show)
        entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        self.entries[key] = entry

    def load_existing_settings(self):
        config_path = Path('plugins/baisound/config.yml')
        admin_path = Path('plugins/baisound/baisound.admin.properties')
        ss_config_path = Path('plugins/SuperStream/config.yml')

        try:
            # 既存の設定を読み込む
            if admin_path.exists():
                with open(admin_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('licenseKey='):
                            self.entries['-LICENSE-'].insert(0, line.split('=')[1].strip())
                        elif line.startswith('token='):
                            self.entries['-TOKEN-'].insert(0, line.split('=')[1].strip())

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = self.yaml.load(f)  # yaml.safe_loadをself.yaml.loadに変更
                    if config and 'tiktok' in config:
                        self.entries['-TIKTOK-ID-'].insert(0, config['tiktok'].get('mytiktokid', ''))

            if ss_config_path.exists():
                with open(ss_config_path, 'r', encoding='utf-8') as f:
                    ss_config = self.yaml.load(f)  # yaml.safe_loadをself.yaml.loadに変更
                    if ss_config and 'Players' in ss_config and ss_config['Players']:
                        self.entries['-MINECRAFT-ID-'].insert(0, ss_config['Players'][0])

        except Exception as e:
            messagebox.showerror('エラー', f'設定の読み込み中にエラーが発生しました:\n{str(e)}')

    def save_settings(self):
        try:
            config_path = Path('plugins/baisound/config.yml')
            admin_path = Path('plugins/baisound/baisound.admin.properties')
            ss_config_path = Path('plugins/SuperStream/config.yml')

            # ディレクトリ作成
            config_path.parent.mkdir(parents=True, exist_ok=True)
            ss_config_path.parent.mkdir(parents=True, exist_ok=True)

            # 設定の保存
            values = {k: v.get() for k, v in self.entries.items()}

            # プロパティファイルの更新（既存の設定を保持）
            save_properties(admin_path, values['-LICENSE-'], values['-TOKEN-'])

            # baisound configの更新（tiktokとtargetPlayersのみ更新）
            self.save_config(config_path, values['-TIKTOK-ID-'], values['-MINECRAFT-ID-'])

            # SuperStream configの更新（StreamersとPlayersのみ更新）
            self.save_ss_config(ss_config_path, values['-TIKTOK-ID-'],
                         values['-MINECRAFT-ID-'])

            messagebox.showinfo('成功', '設定が保存されました')
        except Exception as e:
            messagebox.showerror('エラー', f'エラーが発生しました:\n{str(e)}')

    def save_config(self, path, tiktok_id, minecraft_id):
        try:
            if os.path.exists(path):
                # 既存の設定を読み込む
                with open(path, 'r', encoding='utf-8') as f:
                    existing_config = self.yaml.load(f)

                    # tiktokセクションの更新
                    if 'tiktok' not in existing_config:
                        existing_config['tiktok'] = {}
                    existing_config['tiktok']['mytiktokid'] = str(tiktok_id)  # 文字列として保存
                    existing_config['tiktok']['streamer'] = str(
                        self.streamer_entry.get() if self.is_test.get() else tiktok_id
                    )

                    # targetPlayersの更新
                    existing_config['targetPlayers'] = [str(minecraft_id)]  # 文字列として保存
            else:
                # 新規作成の場合
                existing_config = {
                    'tiktok': {
                        'reconnect_interval': 5,
                        'reconnect_timeout': 16,
                        'mytiktokid': str(tiktok_id),
                        'streamer': str(self.streamer_entry.get() if self.is_test.get() else tiktok_id)
                    },
                    'targetPlayers': [str(minecraft_id)]
                }

            # 設定を保存（改行コードをLFに統一）
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                self.yaml.dump(existing_config, f)

        except Exception as e:
            messagebox.showwarning('警告', f'設定の保存中にエラーが発生しました:\n{str(e)}')

    def save_ss_config(self, path, streamer, player):
        try:
            if os.path.exists(path):
                # 既存の設定を読み込む
                with open(path, 'r', encoding='utf-8') as f:
                    existing_config = self.yaml.load(f)

                    # StreamersとPlayersの更新
                    existing_config['Streamers'] = [streamer]
                    existing_config['Players'] = [player]
            else:
                # 新規作成の場合
                existing_config = {
                    'Streamers': [streamer],
                    'Players': [player],
                    'EnableConsoleLogger': True,
                    'StartOnBoot': True,
                    'CommentListener': {
                        'enableChat': False,
                        'format': "&7<user>: &f<message>"
                    },
                    'GiftListener': {
                        'enabled': True,
                        'SubscriberDoubleAction': False
                    }
                }

            # 設定を保存
            with open(path, 'w', encoding='utf-8') as f:
                self.yaml.dump(existing_config, f)

        except Exception as e:
            messagebox.showwarning('警告', f'設定の保存中にエラーが発生しました:\n{str(e)}')

def main():
    root = tk.Tk()
    app = ConfigApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
