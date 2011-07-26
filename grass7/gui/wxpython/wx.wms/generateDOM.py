from xml.dom.minidom import Document

def prepareDOMServerInfo(servernametextstring, serverurltextstring, usernametextstring, passwordtextstring):
	# Create the minidom document
	doc = Document()
	
	# Create the <serverinfo> base element
	serverinfo = doc.createElement("serverinfo")
	doc.appendChild(serverinfo)
	
	servername = doc.createElement("servername")
	serverinfo.appendChild(servername)
	
	serverurl = doc.createElement("serverurl")
	serverinfo.appendChild(serverurl)
	
	username = doc.createElement("username")
	serverinfo.appendChild(username)
	
	password = doc.createElement("password")
	serverinfo.appendChild(password)
	
	
	servernametext = doc.createTextNode(servernametextstring)
	servername.appendChild(servernametext)
	
	serverurltext = doc.createTextNode(serverurltextstring)
	serverurl.appendChild(serverurltext)
	
	usernametext = doc.createTextNode(usernametextstring)
	username.appendChild(usernametext)
	
	passwordtext = doc.createTextNode(passwordtextstring)
	password.appendChild(passwordtext)
	
	return doc


doc = prepareDOMServerInfo('alpha','beta','gamma','delta')
print doc.toprettyxml(indent = "  ")

