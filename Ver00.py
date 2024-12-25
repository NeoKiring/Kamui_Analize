
# coding: UTF-8

import os
import sys
import time
import wave
import hashlib
import threading
import chardet
import subprocess
import tkinter as tk
from tkinter import filedialog , messagebox
from pydub import AudioSegment

from win32con import *
from win32gui import *
from win32process import *

# 共通設定
waitSec = 1.0
windowName = "VOICEROID＋ 京町セイカ EX"

def convert_to_utf8(inputFile):
    # ファイルのエンコーディングを判別
    with open(inputFile, 'rb') as file:
        raw_data = file.read()
        current_encoding = chardet.detect(raw_data)['encoding']

    # 推定されたエンコーディングでテキストを読み込み、UTF-8に変換する
    with open(inputFile, 'r', encoding=current_encoding) as file:
        content = file.read()
    try:
        # テキストをUTF-8に変換
        utf8_content = content.encode('utf-8')
    except UnicodeEncodeError as e:
        raise UnicodeEncodeError(f"エンコーディング変換エラー: {e}")

    return utf8_content.decode('utf-8')

def get_pure_filename(full_path):
    # フルパスからディレクトリパスを除外し、ファイル名と拡張子を取得
    filename_with_extension = os.path.basename(full_path)
    # ファイル名から拡張子を除外
    pure_filename, _ = os.path.splitext(filename_with_extension)
    return pure_filename

def talk(inputFile,file_path):
    # テキストファイルを読み込み、UTF-8に変換
    inputText = convert_to_utf8(inputFile)

    #入力ファイル名の取得
    filename = get_pure_filename(inputFile)

    # 出力先ディレクトリを入力ファイルと同じフォルダ内のwavフォルダに設定
    outdir = os.path.join(os.path.dirname(file_path), 'wav')
    os.makedirs(outdir, exist_ok=True)

    #tmpファイルの定義
    tmpfile = tmpfile = os.path.join(outdir, "tmp.wav")

    # ファイルが存在してたらやめる
    # UTF-8エンコードされたテキストのハッシュを計算
    outfile = outdir + hashlib.md5(inputText.encode('utf-8')).hexdigest() + ".wav"
    if os.path.exists(outfile):
        return outfile

    while True:
        # VOICEROIDプロセスを探す
        window = FindWindow(None, windowName) or FindWindow(None, windowName + "*")

        # 見つからなかったらVOICEROIDを起動
        if window == 0:
            subprocess.Popen([r"C:\Program Files (x86)\AHS\VOICEROID+\SeikaEX\VOICEROID.exe"])
            time.sleep(3 * waitSec)
        else:
            break

    while True:
        # ダイアログが出ていたら閉じる
        errorDialog = FindWindow(None, "エラー") or FindWindow(None, "注意") or FindWindow(None, "音声ファイルの保存")
        if errorDialog:
            SendMessage(errorDialog, WM_CLOSE, 0, 0)
            time.sleep(waitSec)
        else:
            break

    # 最前列に持ってくる
    SetWindowPos(window, HWND_TOPMOST, 0, 0, 0, 0, SWP_SHOWWINDOW | SWP_NOMOVE | SWP_NOSIZE)

    # 保存ダイアログの操作
    def enumDialogCallback(hwnd, param):
        className = GetClassName(hwnd)
        winText = GetWindowText(hwnd)

        # 保存先を設定
        if GetClassName(hwnd) == "ToolbarWindow32":
            SendMessage(hwnd, WM_SETTEXT, 0, outdir)

        # ファイル名を設定
        if className.count("Edit"):
            SendMessage(hwnd, WM_SETTEXT, 0, filename)

        # 保存する
        if winText.count("保存"):
            SendMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, 0)
            SendMessage(hwnd, WM_LBUTTONUP, 0, 0)

    # 音声の保存
    def save():
        time.sleep(waitSec)

        # ダイアログがあれば操作する
        dialog = FindWindow(None, "音声ファイルの保存")
        if dialog:
            EnumChildWindows(dialog, enumDialogCallback, None)
            return

        # 再試行
        save()

    # VOICEROIDを操作
    def enumCallback(hwnd, param):
        className = GetClassName(hwnd)
        winText = GetWindowText(hwnd)

        # テキストを入力する
        if className.count("RichEdit20W"):
            SendMessage(hwnd, WM_SETTEXT, 0, inputText)

        if winText.count("音声保存"):
            # 最小化解除
            ShowWindow(window, SW_SHOWNORMAL)

            # 保存ダイアログ操作用スレッド起動
            threading.Thread(target=save).start()

            # 保存ボタンを押す
            SendMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, 0)
            SendMessage(hwnd, WM_LBUTTONUP, 0, 0)

    # VOICEROIDにテキストを読ませる
    EnumChildWindows(window, enumCallback, None)

    # プログレスダイアログが表示されている間は待つ
    while True:
        if FindWindow(None, "音声保存"):
            time.sleep(waitSec)
        else:
            break

    # 一時ファイルが存在していたら消す
    try:
        os.remove(tmpfile)
    except:
        pass

    return outfile

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        return talk(file_path)
    else:
        print("ファイルが選択されませんでした。")

def select_folder_and_open_txt_files(filepath):
    # 出力先を入力ファイルと同じフォルダ内のtxtフォルダに自動設定
    folder_path = os.path.join(os.path.dirname(filepath), 'txt')
    os.makedirs(folder_path, exist_ok=True)

    # 指定されたフォルダ内の.txtファイルをリストアップ
    txt_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.txt')])

    # ファイルを昇順に処理
    for filename in txt_files:
        full_path = os.path.join(folder_path, filename)
        talk(full_path,file_path)
        print(f"ファイル名: {filename}書き出し完了")
    
    #　完了メッセージ
    print("フォルダ内のすべてのテキストファイルを音声化しました。")

def split_text_file(filepath, chunk_size=12000):
    success = False
    details = []  # 各ファイルの詳細を保持するリスト
    output_dir = os.path.join(os.path.dirname(filepath), 'txt')  # 出力ディレクトリの設定
    os.makedirs(output_dir, exist_ok=True)  # 出力ディレクトリが存在しなければ作成

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()

        sections = []
        start_index = 0
        while start_index < len(text):
            end_index = start_index + chunk_size
            if end_index < len(text):
                newline_index = text.find('\n', end_index)
                if newline_index != -1:
                    end_index = newline_index + 1
            sections.append(text[start_index:end_index])
            start_index = end_index

        for i, section in enumerate(sections):
            if i < 9:
                output_path = os.path.join(output_dir, f"{os.path.basename(filepath).split('.')[0]}_0{i+1}.txt")
            else:
                output_path = os.path.join(output_dir, f"{os.path.basename(filepath).split('.')[0]}_{i+1}.txt")
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.write(section)
            details.append((len(section), len(section.split())))  # 文字数と単語数をタプルで保存

        success = True
    except Exception as e:
        messagebox.showerror("エラー", f"エラーが発生しました: {e}")
    finally:
        if success:
            details_message = "\n".join([f"ファイル {i+1}: {length} 文字 ({words} 単語)" for i, (length, words) in enumerate(details)])
            messagebox.showinfo("完了", f"ファイルは{len(sections)}部分に分割されました。\n{details_message}")
        return success


def combine_wav_files(folder_path):
    input_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.wav')]
    if not input_files:
        messagebox.showwarning("警告", "選択されたフォルダにはWAVファイルがありません。")
        return False

    success = False  # 成功フラグを初期化
    try:
        # 出力ファイル名を設定（親フォルダに保存し、フォルダ名と同じ名前を使用）
        parent_folder = os.path.dirname(folder_path)
        output_filename = os.path.basename(parent_folder) + '.wav'
        output_file = os.path.join(parent_folder, output_filename)

        # 各入力ファイルを開き、出力ファイルに結合する
        with wave.open(output_file, 'wb') as outfile:
            # 最初のファイルからパラメータを取得
            with wave.open(input_files[0], 'rb') as infile:
                params = infile.getparams()
                outfile.setparams(params)

            # 各ファイルのオーディオフレームを書き込む
            for fname in input_files:
                with wave.open(fname, 'rb') as infile:
                    frames = infile.readframes(infile.getnframes())
                    outfile.writeframes(frames)

        success = True  # 成功フラグをTrueに設定
    except Exception as e:
        messagebox.showerror("エラー", f"ファイルの結合中にエラーが発生しました: {e}")
    finally:
        if success:
            messagebox.showinfo("完了", "ファイルの結合が成功しました。")
        return success

def convert_audio(input_file, output_folder):
    # 出力ファイルのフォーマットはmp3、ビットレートは192k固定
    extension = 'mp3'
    bitrate = '192k'
    output_file = os.path.join(output_folder, os.path.basename(input_file).rsplit('.', 1)[0] + f'.{extension}')
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format=extension, bitrate=bitrate)
    return output_file

def on_convert(input_file,outdir):
    if not input_file:
        messagebox.showerror("エラー", "ファイルが選択されていません。")
        return

    output_folder = outdir
    if not output_folder:
        messagebox.showerror("エラー", "保存先が指定されていません。")
        return

    try:
        output_file = convert_audio(input_file, output_folder)
        messagebox.showinfo("完了", f"変換が完了しました。\n出力ファイル: {output_file}")
    except Exception as e:
        messagebox.showerror("エラー", f"変換中にエラーが発生しました。\n{e}")


def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="テキストファイルを選択", filetypes=[("テキストファイル", "*.txt")])
    root.destroy()
    return file_path

def delete_wav_files(directory):
    """指定されたディレクトリからすべてのWAVファイルを削除します。"""
    # ディレクトリ内の全ファイルとディレクトリのリストを取得
    files = os.listdir(directory)
    
    # 各ファイルに対して処理を行う
    for file in files:
        # ファイルのフルパスを生成
        file_path = os.path.join(directory, file)
        
        # ファイルがWAVファイルかどうかを確認
        if file_path.endswith('.wav'):
            try:
                # ファイルを削除
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

def StartUp_seika():
    # VOICEROIDプロセスを探す
        window = FindWindow(None, windowName) or FindWindow(None, windowName + "*")

        # 見つからなかったらVOICEROIDを起動
        if window == 0:
            subprocess.Popen([r"C:\Program Files (x86)\AHS\VOICEROID+\SeikaEX\VOICEROID.exe"])
            time.sleep(3 * waitSec)
        else:
            print("VOICEROID＋ 京町セイカ EX は既に起動されています。")
            # 最前列に持ってくる
            SetWindowPos(window, HWND_TOPMOST, 0, 0, 0, 0, SWP_SHOWWINDOW | SWP_NOMOVE | SWP_NOSIZE)
        print("VOICEROID＋ 京町セイカ EX の保存先ディレクトリを設定してください。")
    

if __name__ == '__main__':
    #テキストファイルの選択
    file_path = select_file()

    StartUp_seika()
    
    #テキストファイルの分割
    if file_path:
        if not split_text_file(file_path):
            messagebox.showwarning("警告", "ファイル分割中にエラーが発生しました。")
    else:
        messagebox.showwarning("警告", "ファイル選択がキャンセルされたか、エラーが発生しました。")
    
   
    #wavファイル削除
    #カレントディレクトリ
    directory = os.path.dirname(file_path)
    delete_wav_files(directory)
    #wavフォルダ内
    directory = os.path.join(os.path.dirname(file_path), 'wav')
    delete_wav_files(directory)
    
    #分割後のテキストファイルを音声化
    select_folder_and_open_txt_files(file_path)

    #分割化されている音声ファイルを結合
    folder_path = os.path.join(os.path.dirname(file_path), 'wav')
    if folder_path:
        success = combine_wav_files(folder_path)
        if not success:
            messagebox.showwarning("警告", "ファイルの結合に失敗しました。")
    else:
        messagebox.showwarning("警告", "フォルダが選択されていません。")

    #結合したファイルをmp3へ変換
    input_file = os.path.splitext(file_path)[0] + '.wav'
    outdir = os.path.dirname(file_path)
    on_convert(input_file,outdir)

    #wavファイルを削除する（最終ファイル出力後の wavフォルダクリーンナップ処理）
    directory = os.path.dirname(file_path)
    delete_wav_files(directory)
    

    #wavフォルダ内
    directory = os.path.join(os.path.dirname(file_path), 'wav')
    delete_wav_files(directory)
