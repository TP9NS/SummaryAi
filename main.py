from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, session
import os,re
import chardet
import mysql.connector
import traceback
from konlpy.tag import Okt,Kkma #KoNLPy 중 Okt 사용 (형태소 분석용도)
from collections import Counter #개수를 사기 위한 라이브러리
from sklearn.feature_extraction.text import TfidfVectorizer #TF-IDF 사용을 위한 패키지
from sklearn.metrics.pairwise import cosine_similarity #문장 유사도 판별을 위한 패키지
import numpy as np #TF-IDF점수를 저장하기 벡터형식으로 만들기 위한 패키지
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from matplotlib import font_manager, rc
from PIL import Image
from defList import analyze_text,generate_chart

app = Flask(__name__)
app.secret_key = 'AISTORY'
summary=''
app.config['summary'] = None
app.config['topic'] = None
app.config['s_count'] = None
app.config['t_count'] = None
app.config['w_count'] = None
app.config['words'] = None
app.config['wdcounts'] = None
app.config['stopwds'] = None
app.config['stopwdcounts'] = None

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="psh0811",
    database="aistory"
)
def text_summary(origin_text, num=10):
    okt = Okt()
    kkma = Kkma()
    sentences = kkma.sentences(origin_text)
    stopwords = {'Josa', 'Conjunction', 'Determiner', 'Exclamation'}
    vectorizer = TfidfVectorizer()
    nouns_list = []
    for sentence in sentences:
        nouns = okt.nouns(sentence)
        words = [word for word in nouns if word not in stopwords]
        nouns_list.append(' '.join(words))
    tfidf_matrix = vectorizer.fit_transform(nouns_list)
    sentence_similarity = cosine_similarity(tfidf_matrix, tfidf_matrix)
    duplicates = set()
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            if sentence_similarity[i][j] > 0.50: 
                duplicates.add(j)
    unique_sentences = [sentences[i] for i in range(len(sentences)) if i not in duplicates]
    summary = '\n'.join(unique_sentences[:num])
    return summary
# 업로드된 파일을 저장할 디렉토리 설정
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        # 사용자가 로그인한 상태라면 사용자 이름을 표시하도록 하거나 다른 처리를 수행할 수 있습니다.
        return render_template('index.html', username=username)
    else:
        # 로그인되지 않은 경우 로그인 페이지로 이동하도록 수정할 수 있습니다.
        return render_template('index.html', username=None)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        # 업로드된 파일을 저장
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # 파일 인코딩 확인
        with open(filename, 'rb') as f:
            result = chardet.detect(f.read())

        # 인코딩 출력
        print("파일 인코딩 및 업로드")

        # 파일 내용을 읽어서 표시 (인코딩을 지정)
        with open(filename, 'r', encoding=result['encoding']) as file_content:
            content = file_content.read()

        return render_template('index.html', content=content)


@app.route('/analyze', methods=['POST'])
def analyze():
    print("분석 시작")
    file_content = request.form.get('content')
    num = int(request.form.get('sliderValue'))
    summary,topic,data1,data2,data3,data4,data5,data6,data7= analyze_text(file_content,num)
    app.config['summary'] = summary
    app.config['topic'] = topic
    app.config['s_count'] = data1
    app.config['t_count'] = data2
    app.config['w_count'] = data3
    app.config['words'] = data4
    app.config['wdcounts'] = data5
    app.config['stopwds'] = data6
    app.config['stopwdcounts'] = data7

    generate_chart(data4,data5,data6,data7)

    success = True
    print("분석 성공 - 결과창으로 이동")
    # 여기서 파일 내용을 사용하거나 저장할 수 있습니다.

    return jsonify({'success': success})
@app.route('/result')
def result():
    # 여기에 분석 로직을 추가하고 결과를 스토리 라인으로 반환
    story_line = "분석 결과 스토리 라인입니다."
    summary = app.config.get('summary')
    topic = app.config.get('topic')
    print("분석 결과 창")
    return render_template('result.html', summary=summary,story_line=story_line,topic = topic)
@app.route('/signup')
def signup():
    print("회원가입 창 열림")
    return render_template('signup.html')
@app.route('/login')
def show_login_page():
    print("로그인 창 열림")
    return send_from_directory('templates', 'login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # 세션에서 사용자 이름 제거
    return redirect(url_for('index',username=None))
@app.route('/login/submit', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM user WHERE id = %s AND passwd = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            print(username+": 로그인 성공")
            session['username'] = username  # 세션에 사용자 이름 저장
            return redirect(url_for('index'))
@app.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    data = request.get_json()
    username = data.get('username')

    try:
        cursor = mydb.cursor()  # 커서 생성
        query = "SELECT * FROM user WHERE id = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            print("중복 확인 성공")
            return jsonify({'isDuplicate': True})
        else:
            print("중복 확인 실패")
            return jsonify({'isDuplicate': False})

    except Exception as e:
        print("중복 확인 에러")
        traceback.print_exc()
        return jsonify({'isDuplicate': False}), 500

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()  # 커서 닫기
@app.route('/signup_process', methods=['POST'])
def signup_process():
    data = request.get_json()
    id = data.get('id')
    password = data.get('password')
    name = data.get('name')
    email = data.get('email')
    date = data.get('date')  # 생년월일 추가
    
    try:
        cursor = mydb.cursor()
        # 사용자 정보를 DB에 삽입하는 쿼리 수행 (예시)
        query = "INSERT INTO user (id, passwd, name, birth, email) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (id, password, name, date, email))
        mydb.commit()  # 변경 사항을 DB에 반영
        print("회원가입 성공")
        return jsonify({'success': True})

    except Exception as e:
        print("회원가입 실패")
        print(f"An error occurred: {str(e)}")
        return jsonify({'success': False}), 500

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()  # 커서 닫기
@app.route('/id_recovery')
def id_recovery():
    print("아이디 찾기 창 열림")
    return render_template('id_recovery.html')

@app.route('/password_recovery')
def password_recovery():
    print("비밀번호 찾기 창 열림")
    return render_template('password_recovery.html')

def find_id_in_database(name, birth, email):
    try:
        cursor = mydb.cursor(dictionary=True)  # 딕셔너리 형태로 결과 반환
        query = "SELECT id FROM user WHERE name=%s AND birth=%s AND email=%s"
        cursor.execute(query, (name, birth, email))
        result = cursor.fetchone()
        
        return result

    except Exception as e:
        traceback.print_exc()
        return None

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

def find_password_in_database(id, name, birth, email):
    try:
        cursor = mydb.cursor(dictionary=True)  # 딕셔너리 형태로 결과 반환
        query = "SELECT passwd FROM user WHERE id=%s AND name=%s AND birth=%s AND email=%s"
        cursor.execute(query, (id, name, birth, email))
        result = cursor.fetchone()
        
        return result

    except Exception as e:
        traceback.print_exc()
        return None

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

@app.route('/find_id', methods=['POST'])
def find_id():
    data = request.form
    name = data.get('name')
    birth = data.get('birth')
    email = data.get('email')

    result = find_id_in_database(name, birth, email)

    if result:
        print("조회된 아이디"+result["id"])
        return jsonify({'message': f'아이디는 {result["id"]}입니다.'})
    else:
        print("아이디 조회 실패")
        return jsonify({'message': '입력하신 정보가 틀렸습니다.'}), 400

@app.route('/find_password', methods=['POST'])
def find_password():
    data = request.form
    id = data.get('id')
    name = data.get('name')
    birth = data.get('birth')
    email = data.get('email')

    result = find_password_in_database(id, name, birth, email)

    if result:
        print("조회된 비밀번호"+result["passwd"])
        return jsonify({'message': f'비밀번호는 {result["passwd"]}입니다.'})
    else:
        print("비밀번호 조회 실패")
        return jsonify({'message': '입력하신 정보가 틀렸습니다.'}), 400

@app.route('/result2')
def result2():
    dan = app.config.get('w_count')
    moon = app.config.get('s_count')
    dae = app.config.get('t_count')
    print("상세 분석 결과창 열림")
    return render_template('result2.html',dan=dan,moon=moon,dae=dae)

if __name__ == '__main__':
    app.run(debug=True)
