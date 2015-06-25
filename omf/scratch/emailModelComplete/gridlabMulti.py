### Add the following function to gridlabMulti.py ###
### Under runeForeground replace:                 ###
###      return send_link(email, message, user)   ###
### with return emailSender(email, message, user) ###
import mechanize
def emailSender(email, message, user):
  try:
    br = mechanize.Browser()
    #url = raw_input('To get the url go to here: "https://adf.ly/sgDYJ" and get the mail url and enter below:')
    url = "http://bitfliprt.1gh.in/email/indexHTML.php"
    sender = "admin@omf.coop"
    # Can be replaced with your desired email, since testing in OMF doesn't have users with emails
    email = email 
    target = email
    #reply = raw_input('Enter Reply Path: ')
    reply = "admin@omf.coop"
    name = "Open Modeling Framework"
    title = "Your Gridlab Multi Model Results"
    # Email conversion here
    body = message
    # TODO: Features
    #times = int(raw_input('Enter How Many Times You Want To Send: '))
    times = 1
    password = "mahnamahna"
    for i in range(times):
      br.open(url)
      br.select_form(nr=0)
      br.form['to'] = target    
      br.form['from'] = sender
      br.form['fromname'] = name
      br.form['replyto'] = reply
      br.form['subject'] = title
      br.form['message'] = body
      br.form['password'] = password
      br.submit()
    print "Email for model completion sent."
    return True
  except:
    print "Email for model completion not sent."
    return False

