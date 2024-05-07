from konlpy.tag import Okt,Kkma
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter,defaultdict
import os,re;
import matplotlib.pyplot as plt
import chardet
from matplotlib import font_manager, rc
def analyze_text(text,num = 10):
    pattern = re.compile(r'[.?!]')
    sentences = pattern.split(text)
    sentences = sentences[1:]
    text=text
    okt = Okt()
    new_text = ''
    detail_text = ''
    for i in sentences:
        detail_text += i+'.'
        clean_sentence = re.sub('[^가-힣a-zA-Z0-9\s.-?!]', '', i)
        if len(clean_sentence.strip()) < 1:
            continue
            
        new_text += clean_sentence+ '.'

    def detail_analyze(origin,sentences):
        length = len(re.split(r'[.?!]',sentences)) ##문장 수 반환(리턴할 변수)
        #대사 수
        pattern = re.compile(r'“(.*?)”')
        first_type = re.findall(pattern,origin)
        sub_test = re.compile(r'["]+[가-힣a-zA-Z0-9-\s.-?!]+["]')
        matches = re.findall(sub_test,origin)
        talk_length = len(matches) + len(first_type)
       
        #단어 수
        morph = okt.pos(sentences)
        delete = [word[0] for word in morph if word[1] == 'Punctuation']
        morph = [word for word in morph if word[0] not in delete]

        word_length = len(morph)

        #명사TOP 5
        nouns = okt.nouns(sentences)
        stopwords_tags = {'Josa', 'Conjunction', 'Determiner', 'Exclamation'}
        stopwords = [word[0] for word in morph if word[1] in stopwords_tags]
        filtered_nouns = [word for word in nouns if word not in stopwords]
        filtered_word_count = Counter(filtered_nouns)
        top_nouns = filtered_word_count.most_common(5)
        words, wdcounts = zip(*top_nouns)


        #불용어 TOP5
        stopwords_tags = {'Josa', 'Conjunction', 'Determiner', 'Exclamation'}
        stopwords = [word[0] for word in morph if word[1] in stopwords_tags]
        stopword_count = Counter(stopwords)

        top_stop = stopword_count.most_common(5)
        stopWd,stopCount = zip(*top_stop)

        return length,talk_length,word_length,words,wdcounts,stopWd,stopCount
        #순서대로 문장 수,대사 수,단어 수,명사 5개,명사 출현 횟수,불용어,불용어 출현 횟수

   

    def text_summary(origin_text, num=5):
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

    
    def topic_sentence(text, num_sentences=1):
        kkma = Kkma()
        sentences = kkma.sentences(text)  
        sentence_scores = defaultdict(int)
        for sent in sentences:
            sentence_scores[sent] = len(sent)
        top_sentences = sorted(sentence_scores, key=lambda x: sentence_scores[x], reverse=True)[:num_sentences]
        result = ''
        result = top_sentences[0]

        return result

    # 스토리 요약 및 주제 추출 수행
    percent = int((len(sentences) * num) / 100)
    summary = text_summary(new_text,percent)
    topics = topic_sentence(new_text)
    data1,data2,data3,data4,data5,data6,data7 = detail_analyze(detail_text,new_text)

    return summary,topics,data1,data2,data3,data4,data5,data6,data7

def generate_chart(words,wdcounts,stopwds,stopwdcounts):
    # Matplotlib 폰트 설정 (한글 지원을 위해 추가)
    font_path = "C:/Windows/Fonts/malgun.ttf"  # 한글 폰트 경로에 따라 수정
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font_name)
    # 데이터 (임의로 정하셔도 됩니다)
    wdlabels = words ##많이 나오는 단어 5개
    wdvalues = wdcounts ##나온 횟수
    swdlabels = stopwds ##불용어 단어
    swdvalues = stopwdcounts #불용어 횟수
    

    # 많이 나오는 명사 파이차트
    plt.figure(figsize=(5, 5), facecolor='lightblue')
    plt.pie(wdvalues, labels=wdlabels, autopct='%1.1f%%', startangle=90)


    # 많이 나오는 명사 파이 차트 저장1
    img_word_pie_path = 'static//img_word_pie.png'
    plt.savefig(img_word_pie_path)
    plt.close()
    # 많이 나오는 명사 바차트
    plt.figure(figsize=(8, 6), facecolor='lightblue')
    bars = plt.bar(words, wdcounts, color='cyan')

    # 각 막대 위에 정확한 수치 표시 (소수점 없이)
    for bar in bars.patches:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')

    # 이미지 저장2 (단어별 빈도수 바 차트)
    img_word_bar_path =  'static//img_word_bar.png'
    plt.savefig(img_word_bar_path)
    plt.close()
    
    # 불용어 파이 차트
    plt.figure(figsize=(5, 5), facecolor='lightblue')
    plt.pie(swdvalues, labels=swdlabels, autopct='%1.1f%%', startangle=90)


    # 불용어 파이 차트 저장3 
    img_sword_pie_path =  'static//img_sword_pie.png'
    plt.savefig(img_sword_pie_path)
    plt.close()

    # 두 번째 파이차트에서 가장 많이 나오는 불용어 5개 바 차트로 그리기
    plt.figure(figsize=(8, 6), facecolor='lightblue')
    bars = plt.bar(stopwds, stopwdcounts, color='cyan')

    # 각 막대 위에 정확한 수치 표시 (소수점 없이)
    for bar in bars.patches:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')

    # 이미지 저장4 (불용어별 빈도수 바 차트)
    img_sword_bar_path =  'static//img_sword_bar.png'
    plt.savefig(img_sword_bar_path)
    plt.close()

    return img_word_pie_path, img_sword_pie_path, img_word_bar_path,img_sword_bar_path