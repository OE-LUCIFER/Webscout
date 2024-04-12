from flask import Flask, render_template, request
from webscout import WEBS
import arrow

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    keywords = request.args.get('keywords', 'holiday')
    timelimit = request.args.get('timelimit', 'm')
    news_list = []
    with WEBS() as webs_instance:
        WEBS_news_gen = webs_instance.news(
          keywords,
          region="wt-wt",
          safesearch="off",
          timelimit=timelimit,
          max_results=20
        )
        for r in WEBS_news_gen:
            r['date'] = arrow.get(r['date']).humanize()
            news_list.append(r)
    return render_template('news.html', news=news_list, keywords=keywords)

if __name__ == '__main__':
    app.run(debug=True)