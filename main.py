from bs4 import BeautifulSoup as bs
from flask import Flask,render_template,request,jsonify
import logging
from flask_pymongo import PyMongo
import requests

"""Logger configuration to check Database logs"""
DBlogger = logging.getLogger('Database')
DBlogger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
file_hanler = logging.FileHandler('Database.log')
file_hanler.setLevel(logging.ERROR)
file_hanler.setFormatter(formatter)
DBlogger.addHandler(file_hanler)
"""Database Logs Configuration Ends here """

"""Stream handler to get logs on Console"""
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
DBlogger.addHandler(stream_handler)
"""Stream Handler Logs Configuration ends here"""

app = Flask(__name__)

app.config['MONGO_URI'] = "mongodb://localhost:27017/crawlerDB"
mongo = PyMongo(app)

@app.route('/',methods=['GET'])
def homePage():
    return render_template('index.html')


@app.route('/scrappeData',methods=['POST'])
def scrap():
    if request.method == 'POST':
        _json = request.json
        # searchString = _json['searchString']
        searchString_2 = request.form['content'].replace(" ","")
        print(searchString_2)
        # DBlogger.log(searchString)
        # DBlogger.log(request.method)
        try:
            existingReviews = mongo.db.crawlerDb.find_one({'searchString' : searchString_2})
            print(existingReviews)
            try:
                if existingReviews:
                    # return existingReviews
                    return render_template('results.html', reviews=existingReviews)
            except Exception as e:
                DBlogger.exception(e)
                return "Unable to Fetch Data"
            else:
                flipkart_url = "https://www.flipkart.com/search?q="+searchString_2
                uClient = requests.get(flipkart_url)
                flipkartPage = uClient.content
                uClient.close()
                flipkart_html = bs(flipkartPage,"html.parser")
                bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
                del bigboxes[0:3]
                for bigbox in bigboxes:
                    productLink = "https://www.flipkart.com" + bigbox.div.div.div.a['href']
                    prodResp = requests.get(productLink)
                    prod_html = bs(prodResp.content, "html.parser")
                    print(prod_html.prettify())
                    commentboxes = prod_html.findAll('div', {'class': "col _2wzgFH"})
                    reviews = []
                    for commentbox in commentboxes:
                        # DBlogger.log(commentbox)
                        try:
                            name = commentbox.findAll('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                            print(commentbox)
                        except Exception as e:
                            DBlogger.exception(e)
                            name = "No Name"
                        try:
                            rating = commentbox.findAll('p',{'class':'_2-N8zT'})[0].text
                            print(rating)
                        except Exception as e:
                            DBlogger.exception(e)
                            rating = "No Rating"
                        try:
                            commenthead = commentbox.findAll('div',{'class','_3LWZ1K _1BLPMq'})
                            print(commenthead)
                        except Exception as e:
                            DBlogger.exception(e)
                            commenthead = "No Comment head"
                        try:
                            comtag = commentbox.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                            print("comtag Value is ",comtag,"Customer Cumment is ",custComment)
                        except Exception as e:
                            DBlogger.exception(e)
                            custComment = "No Comments available"
                        try:
                            id  = mongo.db.crawlerDb.insert_one({"searchString":searchString_2,"name":name,"rating":rating,"commenthead":commenthead,"custComment":custComment})
                            # DBlogger.log(id)
                            mydict = {"Product": searchString_2, "Name": name, "Rating": rating, "CommentHead": commenthead,"comment": custComment}
                            reviews.append(mydict)
                            # resp = jsonify("Data  fetch and addess Successfully")
                            # resp.status_code = 200
                            return render_template('results.html',reviews=reviews)
                        except Exception as e:
                            DBlogger.exception(e)
        except Exception as e:
            DBlogger.exception(e)
            return "Something Went Wrong"
    else:
        return  not_found()


@app.route("/retriveData",methods = ['POST'])
def retriveComment():
    _json = request.json
    searchString = _json['searchString']
    try:
        if request.method == 'POST':
            data = mongo.db.crawlerDb.find_one({
                'searchString' : searchString })
            print(data)
            jsonifyData = jsonify(data)
            resp = jsonify("Retrive Data Successfully",jsonifyData)
            resp.status_code = 200
            return resp
        else:
            return  not_found()
    except Exception as e:
        DBlogger.exception(e)



@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status' : 404,
        'message': 'Not Found' + request.url
    }
    resp = jsonify(message)
    resp.status_code= 404
    return resp


if __name__ == "__main__":
    app.run(port=8000, debug=True)




