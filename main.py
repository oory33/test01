import tkinter as tk
from tkinter import *
import os
import tkinter.ttk as ttk
import subprocess as sp
import numpy as np
import scipy.io.wavfile as wav

import akeroyd as ak
import modulation as mod

import threading
import time
import sys

shift = 2
duration = 4
srate = 48000
bwd = 800
centre = 600
maximum = 100

LiPath = sys.argv[0].split("/")
initwd = '/'.join(LiPath[:-4])

if os.path.exists(initwd + "/sano_test01"):
    pass
else:
    os.mkdir(initwd + "/sano_test01")

cwd = initwd + "/sano_test01"

if os.path.exists(cwd + "/answ"):
    pass
else:
    os.mkdir(cwd + "/answ")

if os.path.exists(cwd + "/.stimuli"):
    pass
else:
    os.mkdir(cwd + "/.stimuli")
    os.mkdir(cwd + "/.stimuli/up")
    os.mkdir(cwd + "/.stimuli/down")


def rand_2():
    return np.random.randint(0, 2)

# is_A_right, is_ref_rightを入力に、refがAかBかを返す


def is_ref_A_B(is_A_right, is_ref_right):
    if not (is_A_right ^ is_ref_right):
        return "A"
    else:
        return "B"


# A.Bどっちを選択したか
react = ""

# A,B,Rのどのボタンを押したか
btn = ""

# 今何問目？
index = 0

# referenceはどっち？
references_choice = ["left", "right"]

# 今再生中?
playing = FALSE

# 閾値とする正答率
p = 0.5

# 刺激強度の変化のしやすさ
W = 1

# 終了ステップ幅
end_step = 0.015


class Stimuli():
    def __init__(self, file_path, up_down):
        self.fnames = []
        self.file_path = file_path
        self.is_A_right = rand_2()  # 今のstimuli Aはleft/rightどっち？(0ならleft、1ならright)
        self.is_ref_right = rand_2()  # 今のreferenceはどっち？(0ならleft、1ならright)
        self.count = 0  # 何回目の試行か

        self.step = 0.1  # 初期ステップ幅

        if up_down == "down":
            self.vec = -1
            self.depth = 0.8
            self.up_down = "down"  # ステップ幅変更の向き
        elif up_down == "up":
            self.vec = 1
            self.depth = 0.2
            self.up_down = "up"  # ステップ幅変更の向き

        self.react_list = []  # 回答の記録
        self.A_list = []  # lef/rightの記録(0ならAがleft、1ならBがleft)
        self.reference_list = []  # referenceがleftかrightかの記録
        self.asw_list = []  # referenceがAかBかの記録

        self.step_list = []  # ステップサイズの記録
        self.is_correct_list = []  # 正答かどうかの記録
        self.depth_list = []  # 深さの記録
        self.vec_list = []  # ステップ変化方向の記録
        self.is_done = False  # 次の試行を行うか

        self.A = sp.Popen(["printf", ""])
        self.B = sp.Popen(["printf", ""])
        self.R = sp.Popen(["printf", ""])

        self.make_next_stimuli(self.file_path)

        for fname in os.listdir(file_path):
            base, txt = os.path.splitext(fname)
            if txt == ".wav":
                self.fnames.append(fname)

    def play_A(self):
        global playing
        if playing:
            self.A.kill()
            self.B.kill()
            self.R.kill()
            time.sleep(0.2)
            self.A = sp.Popen(["afplay", self.fnames[self.is_A_right+1]])
        else:
            self.A = sp.Popen(["afplay", self.fnames[self.is_A_right+1]])

    def play_B(self):
        global left, playing
        if playing:
            self.A.kill()
            self.B.kill()
            self.R.kill()
            time.sleep(0.2)
            self.B = sp.Popen(["afplay", self.fnames[not (self.is_A_right)+1]])
        else:
            self.B = sp.Popen(["afplay", self.fnames[not (self.is_A_right)+1]])

    def play_R(self):
        global playing
        if playing:
            self.A.kill()
            self.B.kill()
            self.R.kill()
            time.sleep(0.2)
            self.R = sp.Popen(["afplay", self.fnames[0]])
        else:
            self.R = sp.Popen(["afplay", self.fnames[0]])

    def is_correct(self, i):  # i番目の試行で正答したかどうか
        if i >= 0:
            if self.asw_list[i] == self.react_list[i]:
                return True
            else:
                return False
        else:
            return None

    def would_cahnge_step(self):  # ステップ強度を維持するか
        current_step = self.depth_list[-1]
        if self.count < 3:  # 3回までは維持
            return False
        else:
            global p, W
            current_step_index_list = [i for i, x in enumerate(
                self.depth_list) if x == current_step]  # 現在のdepthの試行のindexのリスト
            a = []
            for i in current_step_index_list:
                a.append(self.is_correct(i))
                Nc = sum(a)  # 正答数の和
            ENc = len(current_step_index_list) * p  # 正答数の期待値
            print("Nc:", Nc, "ENc:", ENc, "\n")
            if ENc - W <= Nc <= ENc + W:
                return False
            elif Nc < ENc - W:
                self.vec *= 1
                return True
            elif Nc > ENc + W:
                self.vec *= -1
                return True

    def make_next_coefficients(self):  # 次の刺激の係数決め
        if self.would_cahnge_step():
            a = self.is_correct_list.copy()
            a.reverse()
            t_or_f = self.is_correct(self.count-1)  # 一つ前の回答で正答したか

            if self.vec_list[-1] != self.vec:  # 変化の向きが反転したら半分に
                self.step *= 0.5
            elif self.vec_list[-1] == self.vec:  # 変化の向きが同じならそのまま
                self.step *= 1
            elif self.vec_list[-2] == self.vec_list[-1] == self.vec:  # 3連続で同じ方向に変化したら倍に
                self.step *= 2
            elif not (t_or_f) in self.is_correct_list:  # これまでに一度でも反転しているか
                n = len(a) - a.index(not (t_or_f)) - 1  # 直近の反転が何番目か
                if self.step_list[n] != 2 * self.step_list[n-1]:  # 直近の反転の直前で倍になっていないならそのまま
                    self.step *= 1
                else:  # 直近の反転の直前で倍になっているなら倍に
                    self.step *= 2
            self.depth += self.vec * self.step

        if self.step > 0.2:
            self.step = 0.2  # ステップサイズの上限

        if self.depth > 1:  # depth の上限・下限
            self.depth = 1
        elif self.depth < 0:
            self.depth = 0

    def is_next_alive(self):  # 試行を続行するか？
        if self.step > end_step:
            return True
        else:
            return False

    def is_others_done(self):
        if self.up_down == "up":
            return stim_down.is_done
        elif self.up_down == "down":
            return stim_up.is_done

    def make_next_stimuli(self, file_path):
        global references_choice, srate, duration, shift, direct, bwd, centre
        os.chdir(file_path)
        for direct in references_choice:
            sig = ak.GenrateInitIpd(srate=srate, duration=duration,
                                    shift=shift, bwd=bwd, centre=centre, init_direction=direct, init_ipd=90)
            sig_mod = mod.HalfSinMod(
                signal=sig, srate=srate, freq=shift*2, depth=self.depth)
            out = mod.RaisedCos(signal=sig_mod, srate=srate,
                                beta=0.8, length=100)
            out = out.astype(np.float32)
            wav.write("ak_%a.wav" %
                      direct, srate, out)
        # make reference
        sig = ak.GenrateInitIpd(srate=srate, duration=duration,
                                shift=shift, bwd=bwd, centre=centre, init_direction=references_choice[self.is_ref_right], file_name="reference.wav", init_ipd=90)
        sig_mod = mod.HalfSinMod(
            signal=sig, srate=srate, freq=shift*2, depth=self.depth)
        out = mod.RaisedCos(signal=sig_mod, srate=srate, beta=0.8, length=100)
        out = out.astype(np.float32)
        wav.write("reference.wav", srate, out)

    def save_data(self):
        global react, index, references_choice, btn
        self.react_list.insert(self.count, react)
        self.A_list.insert(self.count, references_choice[self.is_A_right])
        self.reference_list.insert(
            self.count, references_choice[self.is_ref_right])
        self.asw_list.insert(self.count, is_ref_A_B(
            self.is_A_right, self.is_ref_right))
        self.is_correct_list.insert(self.count, self.is_correct(self.count))
        self.depth_list.insert(self.count, self.depth)
        self.step_list.insert(self.count, self.step*self.vec)
        self.vec_list.insert(self.count, self.vec)

        index += 1
        self.count += 1
        self.is_ref_right = rand_2()
        self.is_A_right = rand_2()
        react = ""
        btn = ""

    def output_data(self):
        result = np.vstack(
            [self.A_list, self.react_list, self.reference_list, self.step_list, self.is_correct_list, self.depth_list])
        os.chdir(cwd + "/answ")
        np.savetxt('%s_%a.csv' % (user, self.up_down),
                   result, delimiter=',', fmt='%s')


stim_up = Stimuli(str(cwd + "/.stimuli/up"), "up")
stim_down = Stimuli(str(cwd + "/.stimuli/down"), "down")


class Layer(tk.Frame):
    def __init__(self, master, **kwarg):
        super().__init__(
            master, width=kwarg['width'], height=kwarg['height'])

        self.var = tk.StringVar()  # A.Bどっちを選択したか
        self.error = tk.StringVar()  # 選択せずにNextを押したときのエラー
        self.error.set('')
        self.playing_status = tk.StringVar()  # 再生中かどうかの変数

        label = ttk.Label(self, textvariable=self.var,
                          justify='center', font=("", 80))  # A.Bどっちを選択したか

        label_static = ttk.Label(
            self, text="is reference", font=("", 40))

        label_error = ttk.Label(
            self, textvariable=self.error, font=("", 20))  # 選択せずにNextを押したときのエラー

        label_playing = ttk.Label(
            self, textvariable=self.playing_status, font=("", 24))

        self.A_btn = tk.Button(self, text="A", font=(
            "", 20), command=self.A_btn_clicked)

        self.B_btn = tk.Button(self, text="B", font=(
            "", 20), command=self.B_btn_clicked)

        self.R_btn = tk.Button(self, text="reference", font=(
            "", 20), command=self.R_btn_clicked)

        self.play_btn = tk.Button(self, text="play/pause", font=(
            "", 20), command=self.play_btn_clicked)

        self.next = tk.Button(self, text="next", font=(
            "", 20), command=self.next_btn_clicked)

        self.end_label = ttk.Label(self,
                                   text='実験は以上で終了です',
                                   anchor='center',
                                   font=("", 42))

        if "test" in kwarg:
            self.A_btn.place(x=100, y=400, width=200, height=100)
            self.B_btn.place(x=500, y=400, width=200, height=100)
            self.R_btn.place(x=300, y=300, width=200, height=50)
            self.play_btn.place(x=590, y=50, width=150, height=50)
            self.next.place(x=590, y=150, width=150, height=50)
            label_static.place(x=330, y=230)
            label.place(x=250, y=200)
            label_error.place(x=290, y=100)
            label_playing.place(x=100, y=20)
        elif "end" in kwarg:
            self.end_label.place(x=220, y=300, height=100)
        elif "entry" in kwarg:
            self.entry = ttk.Entry(self, width=20, font=("", 30))
            self.entry.insert(tk.END, "名前を入力してください")
            self.entry.place(x=150, y=230, width=400, height=100)
            self.entry.bind('<Return>', self.entry_btn_clicked)
            self.entry_btn = tk.Button(self, text="OK", font=(
                "", 20), command=self.entry_btn_clicked)
            self.entry_btn.place(x=550, y=230, width=100, height=100)

    def entry_btn_clicked(self):
        global user
        user = self.entry.get()
        self.entry.destroy()
        self.entry_btn.destroy()
        self.destroy()

    def A_btn_clicked(self):  # Aボタンが押されたときの処理
        global react, btn
        btn = "A"
        react = "A"  # reactにAを代入
        self.clicked_answ()
        self.play()

    def B_btn_clicked(self):  # Bボタンが押されたときの処理
        global react, btn
        btn = "B"
        react = "B"  # reactにBを代入
        self.clicked_answ()
        self.play()

    def R_btn_clicked(self):  # referenceボタンが押されたときの処理
        global btn
        global react, index
        if index % 2 == 0:  # indexが偶数のとき
            stim = stim_up
        else:  # indexが奇数のとき
            stim = stim_down
        stim.output_data()
        btn = "R"
        self.play()

    def play_btn_clicked(self):  # play/pauseボタンが押されたときの処理
        global react, index
        if index % 2 == 0:  # indexが偶数のとき
            stim = stim_up
        else:  # indexが奇数のとき
            stim = stim_down
        if playing == FALSE:
            self.play()
        else:  # 再生中なら停止
            stim.A.kill()
            stim.B.kill()
            stim.R.kill()

    def next_btn_clicked(self):  # nextボタンが押されたときの処理
        global index, react, playing
        if index % 2 == 0:  # indexが偶数のとき
            stim = stim_up
        else:  # indexが奇数のとき
            stim = stim_down
        if react != "":  # reactが空でないとき（ABどちらかを選択した場合）
            stim.save_data()  # データを格納
            self.var.set('')  # ABの選択をリセット
            stim.A.kill()
            stim.B.kill()
            stim.R.kill()
            playing = FALSE
            if stim.is_done == False:
                stim.make_next_coefficients()
                if stim.is_next_alive():
                    stim.make_next_stimuli(stim.file_path)
                elif stim.is_next_alive() == False:
                    stim.is_done = True
            elif stim.is_done:
                if stim.is_others_done():
                    stim.output_data()
                    end.tkraise()
                elif stim.is_others_done() == False:
                    # self.next_btn_clicked()
                    stim.make_next_stimuli(stim.file_path)
            if index >= maximum:
                stim.output_data()
                stim.is_done = True
                if stim.is_others_done():
                    end.tkraise()
        else:
            self.error.set("Please select an answer")

    def clicked_answ(self):  # AかBが選択されたときの処理
        global react
        self.var.set(react)  # 選択したものを表示
        self.error.set('')

    def play(self):  # 再生
        global react, btn, index
        if index % 2 == 0:  # 偶数のとき
            stimuli = stim_up
            os.chdir("/Users/ryo/Documents/python/M/test01/stimuli/up")
        else:  # 奇数のとき
            stimuli = stim_down
            os.chdir("/Users/ryo/Documents/python/M/test01/stimuli/down")

        if btn == "A":  # AかBかRで再生するものを変える
            stimuli.play_A()
        elif btn == "B":
            stimuli.play_B()
        elif btn == "R":
            stimuli.play_R()
        else:  # AかBが選択されていないとき
            self.error.set('Please select a stimulus')


app = tk.Tk()
app.title("test01")
app.geometry("800x600")
entry_init = Layer(app, width=800, height=600, entry=True)
entry_init.grid(row=0, column=0, sticky="nsew")
trial_init = Layer(app, width=800, height=600, test=True)
trial_init.grid(row=0, column=0, sticky="nsew")
end = Layer(app, width=800, height=600, end=True)
end.grid(row=0, column=0, sticky="nsew")
trial_init.tkraise()
entry_init.tkraise()


def watching():
    global playing, index
    while True:
        if index % 2 == 0:  # indexが偶数のとき
            stim = stim_up
        else:  # indexが奇数のとき
            stim = stim_down
        if stim.A.poll() is None:
            playing = TRUE
            trial_init.playing_status.set("now playing A")
        elif stim.B.poll() is None:
            playing = TRUE
            trial_init.playing_status.set("now playing B")
        elif stim.R.poll() is None:
            playing = TRUE
            trial_init.playing_status.set("now playing Reference")
        else:
            playing = FALSE
            trial_init.playing_status.set("")
        time.sleep(0.05)


watching_status = threading.Thread(target=watching)
watching_status.start()

app.mainloop()
