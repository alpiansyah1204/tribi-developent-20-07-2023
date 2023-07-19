from flask import Flask,request,jsonify, render_template,Response    
# from camera import VideoCamera
import time,string, cv2
from moviepy.editor import *
# import StemmerFactory class
from fastDamerauLevenshtein import damerauLevenshtein
import pandas as pd
    
app = Flask(__name__,static_folder='static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
# video_stream = VideoCamera()

imbuhan = ['ber', 'ter', 'se', 'ke', 'di', 'pe', 'me','wati','nya', 'wan', 'man','kan', 'ti', 'an','pun', 'lah', 'kah']
list_animation = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
df = pd.read_csv('data/kbbi.txt',header=None, names=['kata'])
df = df.dropna()
imbuhan_awal = ['ber', 'ter', 'se', 'ke', 'di', 'pe', 'me']
imbuhan_akhir = ['wati','nya', 'wan', 'man','kan', 'ti', 'an']
imbuhan_partikel =  ['pun', 'lah', 'kah']
df_akronim = pd.read_csv('data/persamaan.csv')

def hapus_angka(string_input):
    string_tanpa_angka = ''.join(char for char in string_input if not char.isdigit())
    return string_tanpa_angka

def case_folding(string_input):
    string_input = string_input.lower()
    return string_input

def hapus_tanda_baca(string_input):
    translator = str.maketrans("", "", string.punctuation)
    string_tanpa_tanda_baca = string_input.translate(translator)
    return string_tanpa_tanda_baca

def animation(word):
    print([fr'{i}.mp4' for i in word])
    video =[]
    for i in word:
        if i in list_animation:
            video.append(VideoFileClip(fr'videos/abjad/{i}.mp4'))
        elif i in imbuhan_awal:
            video.append(VideoFileClip(fr'videos/imbuhan/awalan/{i}.mp4'))
        elif i in imbuhan_akhir:
            video.append(VideoFileClip(fr'videos/imbuhan/akhiran/{i}.mp4'))
        elif i in imbuhan_partikel:
            video.append(VideoFileClip(fr'videos/imbuhan/partikel/{i}.mp4'))
    # video = [ VideoFileClip(fr'videos/abjad/{i}.mp4') for i in word]
    # # join and write
    result = concatenate_videoclips(video)
    result.write_videofile('video/combined.mp4',30)

def longest_common_substring(str1, str2):
    len_str1 = len(str1)
    len_str2 = len(str2)
    lcs_matrix = [[0] * (len_str2 + 1) for _ in range(len_str1 + 1)]

    for i in range(1, len_str1 + 1):
        for j in range(1, len_str2 + 1):
            if str1[i-1] == str2[j-1]:
                lcs_matrix[i][j] = lcs_matrix[i-1][j-1] + 1
            else:
                lcs_matrix[i][j] = max(lcs_matrix[i-1][j], lcs_matrix[i][j-1])

    return lcs_matrix[len_str1][len_str2]

def choose_string(input_string, string_list):
    max_lcs = 0
    selected_string = ''

    for string in string_list:
        lcs_length = longest_common_substring(input_string, string)
        if lcs_length > max_lcs:
            max_lcs = lcs_length
            selected_string = string

    return selected_string

def damerau_levenshtein_distance(str1, str2):
    return damerauLevenshtein(str1, str2,similarity=False)

def spell_correction(kata, df):
    min_distance = float('inf')
    min_word = kata
    
    def calculate_distance(row):
        nonlocal min_distance, min_word
        distance_val = damerau_levenshtein_distance(kata, row['kata'])
        if distance_val < min_distance:
            min_distance = distance_val
            min_word = row['kata']
    
    df.apply(calculate_distance, axis=1)
    
    return min_word

def spell_suggest(kata, df):
    suggestions = []
    
    def calculate_distance(row):
        if damerau_levenshtein_distance(kata, row['kata']) == 1:
            suggestions.append(row['kata'])
    
    df.apply(calculate_distance, axis=1)
    
    return suggestions


def cek_kata(word):
    if df['kata'].isin([word]).any():
        return word 
    
    suggestions = spell_suggest(word, df)
    if suggestions:
        return choose_string(word,suggestions)
    else:
        # Spell correction
        correction = spell_correction(word, df)
        # print(f"{word} ejaan21 yang salah. Mungkin yang dimaksud adalah: {correction}")
        return correction
def cek_string_mengawali(daftar, string):
    for elemen in daftar:
        if string.startswith(elemen):
            return elemen
    return None

def textToAnimation(kata):
    imbuhan_akhir_n_avail = True
    imbuhan_awal_n_avail = True
    imbuhan_partikel_n_avail = True
    hasil = []
    if kata in list_animation:
        hasil.append(kata)
    else :
        for i in imbuhan_awal:
            if kata.startswith(i):
                imbuhan_awal_n_avail = False
                hasil.append(i)
                kata = kata[len(i):]
                break
        
        for i in imbuhan_akhir:
            if kata.endswith(i):
                kata = kata[:-len(i)]
                imbuhan_akhir_n_avail = False
                if kata in list_animation:
                    hasil.append(kata)
                else :
                    for j in kata:
                        hasil.append(j)
                hasil.append(i)
                break
        if(imbuhan_akhir_n_avail):
            for i in imbuhan_partikel:
                if kata.endswith(i):
                    imbuhan_partikel_n_avail = False
                    kata = kata[:-len(i)]
                    if kata in list_animation:
                        hasil.append(kata)
                    else :
                        for j in kata:
                            hasil.append(j)
                    hasil.append(i)
                    break
     
     
        if(imbuhan_akhir_n_avail and imbuhan_partikel_n_avail and imbuhan_awal_n_avail):
            if kata in list_animation:
                        hasil.append(kata)
            else :
                for j in kata:
                    hasil.append(j)
        elif(imbuhan_akhir_n_avail and imbuhan_partikel_n_avail ):
            if kata in list_animation:
                hasil.append(kata)
            else :
                for j in kata:
                    hasil.append(j)
    hasil.append('idle')
    return hasil

def flatten_list(nested_list):
    flattened = []
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened


def trimKataImbuhan(word):
    word = hapus_angka(case_folding(hapus_tanda_baca(word)))
    li = list(filter(None, word.split(" ")))
    word_sequence = []
    list_word_correction = []
    for i in li:
        print(i)
        if i in df_akronim['singkatan'].values:
            kata = df_akronim.loc[df_akronim['singkatan'] == i, 'kata'].values[0]
            print(f"Kata untuk singkatan '{i}' adalah '{kata}'")
            word_sequence.append(kata)
            list_word_correction.append(kata)
            print('kata',kata)
        else:
            found = False
            for j in imbuhan:
                if i.startswith(j):
                    filtered_df = df.loc[df['kata'] == i, 'kata']
                    if len(filtered_df) > 0:
                        recomendation = cek_kata(i)
                        print('j in imbuhan',i)
                        word_sequence.append(j)
                        word_sequence.append(filtered_df.values[0][len(j):])
                        # list_word_correction.append(j)
                        # list_word_correction.append(recomendation[len(j):])
                        list_word_correction.append(filtered_df.values[0])
                        found = True
                        break
                   
            if not found:
                word_sequence.append(cek_kata(i))
                list_word_correction.append(cek_kata(i))
                print('not found',i)
    return word_sequence, list_word_correction, li

@app.route('/animasi',methods= ['GET'])
def animasi():
    word = request.form['word'] 
    trim = trimKataImbuhan(word)
    textanimasi = textToAnimation(trim)
    animation(textanimasi)    
    
    return  jsonify({'video' : '/video_testing','text' : f'{word}'})

@app.route('/')
def index():
    return 'hello world '

@app.route('/testing')
def testing():
    return render_template('video.html')

text_sequence =[]
@app.route('/video',methods= ['POST','GET'])
def video():
    global text_sequence
    if request.method == 'POST':
        recomendation = ''
        word = request.form['word'] 
        trim,correction,word_input  = trimKataImbuhan(word)
        print('correction' ,correction)
        # text_toanimate = textToAnimation(word_input)
        textToAnimate = [textToAnimation(i) for i in word_input]
        flattenedToAnimation = [item for sublist in textToAnimate for item in (flatten_list(sublist) if isinstance(sublist, list) else [sublist])]

        animation(flattenedToAnimation)   
        url =  "/video_feed"
        print(url)
        recomendation = ""
        print('word_input',word_input)
        print('correction',correction)
        if word_input != correction:
        # Bandingkan list
            recomendation = " ".join(correction)
        print('recomendation',recomendation)
        return jsonify({'url': url, 'text': flattenedToAnimation,'recomendation':recomendation})
    elif request.method == 'GET':
        url =  "/video_feed_idle"
        print(url)
        return render_template('video.html', url=url,text = text_sequence)
    

@app.route('/text_stream')
def text_stream():
    return Response(generate_text(), mimetype='text/event-stream')

def generate_text():
    global textanimasi
    while True:
        # Yield the current state of the textanimasi list as a server-sent event
        yield f"data: {', '.join(textanimasi)}\n\n"

last_frame = None
current_frame = 0
video_status = "stop"
def generate_frames(video_path):
    global current_frame , last_frame, video_status
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    
    while True:
        success, frame = video.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            last_frame = buffer.tobytes()
            time.sleep(0.55/fps)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + last_frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    def generate():
        with open("video/combined.mp4", "rb") as fw:
            data = fw.read(1024)
            while data:
                yield data
                data = fw.read(1024)
    return Response(generate(), mimetype="video/mp4")

@app.route('/video_feed_idle')
def video_feed_idle():
    def generate():
        with open("videos/abjad/idle.mp4", "rb") as fw:
            data = fw.read(1024)
            while data:
                yield data
                data = fw.read(1024)
    return Response(generate(), mimetype="video/mp4")


@app.route('/video_list/<filename>')
def video_feed_list(filename):
    def generate():
        directory =""
        if filename.lower() in list_animation:
            directory = 'abjad'
        elif filename.lower() in imbuhan_awal:
            directory = 'imbuhan/awalan'
        elif filename.lower() in imbuhan_akhir:
            directory = 'imbuhan/akhiran'
        elif filename.lower() in imbuhan_partikel:
            directory = 'imbuhan/partikel'
        with open(f"videos/{directory}/{filename}.mp4", "rb") as fw: 
            data = fw.read(1024)
            while data:
                yield data
                data = fw.read(1024)

    return Response(generate(), mimetype="video/mp4")


@app.route('/abjad')
def abjad_page():
    return render_template('abjad.html')
@app.route('/imbuhan')
def imbuhan_page():
    return render_template('imbuhan.html')

@app.route('/list_video_app/<letter>')
def list_video_app(letter):
    return render_template('video_list.html',letter=letter)


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000) 