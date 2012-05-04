import urllib
import re
import functools

import rdflib
from rdflib.resource import Resource

import oauth2 as oauth


ACCEPT_N3={ "Accept": "text/n3" }

RDF=rdflib.RDF
RDFS=rdflib.RDFS
SEARCH=rdflib.Namespace("http://www.cluug.com/ns/2010/06/search#")
ADMIN=rdflib.Namespace("http://www.cluug.com/admin#")
NIE=rdflib.Namespace("http://www.semanticdesktop.org/ontologies/2007/01/19/nie#")
NAO=rdflib.Namespace("http://www.semanticdesktop.org/ontologies/2007/08/15/nao#")
NCO=rdflib.Namespace("http://www.semanticdesktop.org/ontologies/2007/03/22/nco#")
NFO=rdflib.Namespace("http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#")
PIMO=rdflib.Namespace("http://www.semanticdesktop.org/ontologies/2007/11/01/pimo#")

def nodeOrLiteral(x): 
    if isinstance(x,rdflib.term.Node): return x
    return rdflib.Literal(x)
        

class Thing(Resource): 

    def __init__(self, g, uri):

        if not isinstance(uri, rdflib.term.Identifier): 
            uri=rdflib.URIRef(uri)

        _g=rdflib.Graph(namespace_manager=g.namespace_manager)

        if g:
            _g+=g.triples((uri, None,None))
            _g+=g.triples((None,None,uri))

        Resource.__init__(self, _g, uri)

    def _prop(prop):
        g=lambda self: self.value(prop)
        s=lambda self, x: self.set(prop,nodeOrLiteral(x)
)
        return property(g,s,doc="Functional RDF property <%s>")

    def _propset(prop):
        g=lambda self: self.objects(prop)
        s=lambda self, x: self.add(prop,nodeOrLiteral(x))
        return property(g,s,doc="Set RDF property <%s>")


    label=_prop(RDFS.label)

    creator=_prop(PIMO.creator)
    isAnswered=_prop(PIMO.isAnswered)
    question=_prop(PIMO.question)
    isRelated=_propset(PIMO.isRelated)

    created=_prop(NAO.created)
    lastModified=_prop(NAO.lastModified)
    description=_prop(NAO.description)

    websiteUrl=_prop(NCO.websiteUrl)
    fullname=_prop(NCO.fullname)
    emailAddress=_prop(NCO.emailAddress)

    bookmarks=_prop(NFO.bookmarks)

    mimeType=_prop(NIE.mimeType)    

    fileName=_prop(NFO.fileName)
    filePath=_prop(NFO.filePath)
    fileSize=_prop(NFO.fileSize)
    fileCreated=_prop(NFO.fileCreated)
    fileLastModified=_prop(NFO.fileLastModified)
        
    rdfvalue=_propset(RDF.value)
    rdftype=_prop(RDF.type)

    username=_prop(ADMIN.username)
    email=_prop(ADMIN.username)
    dateJoined=_prop(ADMIN._dateJoined)
    lastLogin=_prop(ADMIN._lastLogin)

    uri=Resource.identifier
    
class Refinder(object): 

    def __init__(self, consumer_key, consumer_secret, oauth_token, oauth_token_secret, baseuri="http://www.getrefinder.com"):
        self.baseuri=baseuri

        self.consumer = oauth.Consumer(consumer_key, consumer_secret)
        self.token=oauth.Token(oauth_token, oauth_token_secret)
        self.client = oauth.Client(self.consumer, self.token)

    def load(self, uri): 
        print "Loading ",uri
        res=self.client.request(uri, headers=ACCEPT_N3)
        print res[1]
        g=rdflib.Graph()
        g.parse(data=res[1], format='n3')
        return g

    def get_user_info(self): 
        g=self.load("%s/data/admin/userinfo/"%self.baseuri)
        # there is one and only one user, hopefully :)
        u=g.subjects(RDF.type, ADMIN.User).next() 
        return Thing(g, u)

    def get_thing(self, thinguri): 
        g=self.load(thinguri)
        return Thing(g,thinguri)

    def get_full_text(self, thinguri): 
        try: 
            uuid=re.search("things/(.*)/#t",thinguri).groups()[0]
            return self.client.request("%s/data/things/%s/fulltext/"%(self.baseuri, uuid))[1]
        except: 
            raise
            #raise Exception("That doesn't look like a Refinder Thing URI: "+thinguri)

    def search(self, query): 
        u="%s/things/search/?q=%s"%(self.baseuri, urllib.quote_plus(query))
        g=self.load(u)

        result=g.subjects(RDF.type, SEARCH.ResultSet).next()
        return [Thing(g,g.value(x,SEARCH.item)) for x in g.transitive_objects(result, SEARCH.next)]

    
        
        
