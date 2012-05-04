import sys

from flask import Flask, render_template, session, url_for, request, redirect, flash

from flaskext.oauth import OAuth

import urllib

sys.path.append("..") # pretty!
from refinder import Refinder

import rdflib

import config



app=Flask('RefinderRecommender')
app.secret_key='veryverysecret'

from jinja2 import contextfilter, Markup


oauth=OAuth()
refinder = oauth.remote_app('refinder',
    base_url='http://getrefinder.com/',
    request_token_url='http://www.getrefinder.com/oauth/request_token',
    access_token_url='http://www.getrefinder.com/oauth/access_token',
    authorize_url='http://www.getrefinder.com/oauth/authorize',
    consumer_key=config.consumer_key,
    consumer_secret=config.consumer_secret
)

@refinder.tokengetter
def get_refinder_token():
    return session.get('refinder_token')

@app.route("/")
def index(): 
    if session.get('refinder_token',False): 
        return render_template("user.html", user=session["refinder_user"])
    else: 
        return render_template("index.html")

def getRefinder(): 
    return Refinder(config.consumer_key, config.consumer_secret, 
                    session['refinder_token'][0], 
                    session['refinder_token'][1])

@app.route("/search")
def search(): 
    r=getRefinder()
    q=request.args['q']
    
    results=r.search(q)
    
    return render_template("user.html", 
                           results=results, 
                           q=q, 
                           user=session["refinder_user"])
    

@app.route('/login')
def login():
    session['next']=request.args.get('next') or request.referrer or None
    return refinder.authorize(callback=url_for('oauth_authorized'))

@app.route('/logout')
def logout(): 
    session.clear()
    flash('Signed out')
    return redirect(url_for("index"))

@app.route('/oauth_authorized')
@refinder.authorized_handler
def oauth_authorized(resp):
    next_url = session['next'] or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['refinder_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    r=getRefinder()
    session['refinder_user'] = r.get_user_info().username

    #flash('You were signed in as %s' % resp['screen_name'])
    flash('Signed in as %s!'%session['refinder_user'])
    return redirect(next_url)

@app.route("/thing")
def thing(): 
    r=getRefinder()    
    
    t=r.get_thing(request.args['uri'])
    return render_template("thing.html", t=t)

@app.route("/user")
def user(): 
    r=getRefinder()    
    
    g=r.get_user_info()
    return render_template("rdf.html", rdf=g.serialize(format='n3'))

@app.route("/text")
def text(): 
    uri=request.args.get("uri")
    r=getRefinder()
    return r.get_full_text(uri)


# from https://github.com/mitsuhiko/jinja2/issues/17#issuecomment-5385981
@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return Markup(s)

if __name__=='__main__':
    app.run(debug=True)
