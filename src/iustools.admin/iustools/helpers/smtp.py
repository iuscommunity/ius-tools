
import smtplib
from cement.core.namespace import get_config
from cement.core.log import get_logger

log = get_logger(__name__)
config = get_config()

def send_mail(to_addr, subject, message):
    log = get_logger(__name__)
    log.debug('Sending mail to %s - %s' % (to_addr, subject))
    config = get_config()
    from_addr = config['admin']['smtp_from']
    subject_prefix = config['admin']['smtp_subject_prefix']
    host = config['admin']['smtp_host']
    port = config['admin']['smtp_port']
    user = config['admin']['smtp_user']
    password = config['admin']['smtp_password']
    tls = config['admin']['smtp_tls']
    key = config['admin']['smtp_keyfile']
    cert = config['admin']['smtp_certfile']
    try:
        smtp = smtplib.SMTP(host, port)
        if tls:
            smtp.starttls(keyfile, certfile)

        if user:
            smtp.login(user, password)

        msg = "From: %s\r\n" % from_addr
        msg = msg + "To: %s\r\n" % to_addr
        msg = msg + "Subject: %s%s\r\n" % (subject_prefix, subject)
        msg = msg + message
        smtp.sendmail(from_addr, to_addr, msg)
    except socket.error, e:
        log.error("unable to send email - %s %s" % (e.args[0], e.args[1]))