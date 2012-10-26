#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import httplib, urllib,  ConfigParser,  argparse,  os.path,  datetime,  zipfile,  types

def get_config_name():
    """ Getting name of config file (in program dir)
    """
    fileName, fileExtension = os.path.splitext(__file__)
    fileName = fileName + '.ini'
    return fileName
    
def get_headers(user_name,  password,  tiddlyname):
    """ HTTP headers
    """
    fullname = tiddlyname + '.tiddlyspace.com'
    url = 'http://' + fullname
    post_data_login = {
        "user": user_name, 
        "password": password , 
        "csrf_token": "", 
        "tiddlyweb_redirect": "/status"}    
    header_login = {
               "Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
               "Accept": "*/*",
               "Origin": url,
               "X-ControlView": "false", 
               "X-Requested-With": "XMLHttpRequest",
               "Referer": url }
    header_download = {
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Charset": "windows-1251,utf-8;q=0.7,*;q=0.3", 
               "Accept-Encoding": "deflate,sdch", 
               "Accept-Language": "en-US,en;q=0.8,ru;q=0.6", 
               "Cookie": "", 
               "rName": user_name,
               "Host": fullname, 
               "Referer": url }
    return header_login,  post_data_login,  header_download

def find_tuple(lst, value):
    """ Find tuple with value
    """
    for line in lst:
        if type(line) is types.ListType:
            return find_list(line,  value)
        else:
            if line == value:
                return lst

#ToDo
def get_cookie(header):
    """ Extract cookie from response header
    """
    cookie_string = ''
    for tup in header:
        if 'set-cookie' in tup:
            for e in tup:
                if e != 'set-cookie':
                    cookie_string = e
                    break
        if cookie_string:
            break
    return cookie_string
    
def parse_command_line():
    """ Parse command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-space_name', dest='space_name',  metavar='',  help='a TiddlySpace name')
    parser.add_argument('-user_name', dest='user_name',  metavar='',  help='an user name')
    parser.add_argument('-password', dest='password',  metavar='',  help='a password')
    parser.add_argument('-backup_path', dest='backup_path',  metavar='',  help='a path for backup file')
    parser.add_argument('--timestamp', dest='timestamp',  action='store_true',   default=False,  help='use timestamp in filename')
    parser.add_argument('--zip', dest='zip',  action='store_true',  default=False, help='zipping a file')
    
    return parser,  parser.parse_args( )
        

def get_config():
    """ Determine config - command line (if exist) or config file
    """
    config = ConfigParser.ConfigParser()
    
    # Parse command line
    parser,  args = parse_command_line()
    if args.space_name != None:        
        config.add_section(args.space_name)
        if args.user_name != None:
            config.set(args.spacename, 'user_name', args.user_name) 
        if args.user_name != None and args.password != None:
            config.set(args.spacename, 'password', args.password) 
        if args.backup_path != None:
            config.set(args.spacename, 'backup_path', args.backup_path) 
        config.set(args.spacename, 'timestamp', args.timestamp) 
        config.set(args.spacename, 'zip', args.zip) 
    
    # Load config file
    if not config.sections():
        try:
            config.read(get_config_name())
        except:
            pass
    
    # Usage help
    if not config.sections() :
        parser.print_help( )
        return None
    return config
    
def get_html(config,  tiddlyname):
    """ Getting a HTML-file
    """
    fullname = tiddlyname + ".tiddlyspace.com"
    url = 'http://' +  fullname
    user_name = config.get(tiddlyname,  'user_name') if config.has_option(tiddlyname,  'user_name') else ''
    password = config.get(tiddlyname,  'password') if config.has_option(tiddlyname,  'password') else ''
 
    conn = httplib.HTTPConnection(fullname)
    header_login,  post_data_login,  header_download = get_headers(user_name,  password,  tiddlyname)
    #conn.set_debuglevel(3)
    
    # Login
    params = urllib.urlencode(post_data_login)
    conn.request("POST", "/challenge/tiddlywebplugins.tiddlyspace.cookie_form", params, header_login)
    response = conn.getresponse()
    header = response.getheaders()
    cookie_val = get_cookie(header)    
    data = response.read()
    
    # Getting file 
    header_download["Cookie"] = cookie_val    
    conn.request("GET", "/tiddlers.wiki?download=" + tiddlyname + '.html', "", header_download)
    response = conn.getresponse()    
    data = response.read()
    conn.close()
    return data

def get_timestamp():
    timestamp = datetime.datetime.today()
    return timestamp.strftime('%Y%m%d-%H%M')
 
def save_file(config,  tiddlyname,  data):
    # Backup path
    if config.has_option(tiddlyname,  'backup_path'):
        backup_path = config.get(tiddlyname,  'backup_path') 
    else:
        backup_path = os.path.abspath(os.path.dirname(__file__))
    # Options
    use_timestamp = config.get(tiddlyname,  'timestamp') if config.has_option(tiddlyname,  'timestamp') else False
    use_zip = config.get(tiddlyname,  'zip') if config.has_option(tiddlyname,  'zip') else False
    timestamp = get_timestamp() if use_timestamp else ''
    # Filename
    filename = tiddlyname + timestamp + ".html"
    filename_full = os.path.join(os.path.abspath(backup_path), filename)
    # Save
    html_file = open(filename_full, 'w')
    print(data, file = html_file)
    html_file.close()
    
    # To zip...
    if use_zip:
        # Zipping
        filename_full_zip = filename_full + '.zip'
        with zipfile.ZipFile(filename_full_zip, 'w',  compression = zipfile.ZIP_DEFLATED) as myzip:
            myzip.write(filename_full,  filename)
        # Delete original file
        os.remove(filename_full)
        filename_full = filename_full_zip
        
    return filename_full

def main(): 
    # Get a configuration
    config = get_config()
    if not config:
        return 0        
    
    # Download
    for tiddlyname in config.sections():
        print('Tiddlyspace: ',  tiddlyname)
        
        data = get_html(config,  tiddlyname)
        filename_full = save_file(config,  tiddlyname, data)
        
        print('     Downloaded file: ',  filename_full)        

    
    
if __name__ == "__main__":
    main()
