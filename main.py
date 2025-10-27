import threading
import time
import os
import webbrowser
import imaplib, email
from email.header import decode_header

#yahoo: imap.mail.yahoo.com
#gmail: imap.gmail.com

#email-id, app-password, mail-imap-server, no. of emails, whether to fetch for this email or not
mails = [["email-id", "app-password", "mail-imap-server", 30, True, 'ALL'],
         ["email-id", "app-password", "mail-imap-server", 30, True, 'ALL'],
         ["email-id", "app-password", "mail-imap-server", 30, True, 'ALL']]

fetched_mails = {}

""" THREAD FUNCTIONS """
#returns the number of threads, no. of files for each thread and correction factor
#correction factor exists to get the correct number of files for even number of threads
def thread_groups(threads, num):
    return threads, int(num), int((num%1 * threads))

#gets the amount of threads to execute for file fetching
def get_thread_amount(num):
    n = 0
    while (num > 10):   #tries to make enough threads to keep time consumed around 10 seconds
        num = num/2
        n += 1

    return thread_groups(2**n, num)

""" SETUP FUNCTIONS """
def setup_SSL_server(server):
    return imaplib.IMAP4_SSL(server)                            #creates server object

def authorise_creds(mail, creds):
    mail.login(creds[0], creds[1])                              #logs in using email id and pass

def select_folder(mail, folder):
    mail.select(folder, readonly = True)                        #selects which folder to search in

def search_folder(mail, search_criteria = 'ALL'):
    return mail.search(None, search_criteria)                   #searches in that folder according to criteria

""" MESSAGE DECODING """
def decode_header_value(encoded):
    decoded = decode_header(encoded)                            #returns tuple as (decoded part as bytes type, encoding used)
    msg_parts = []
    for part, encoding in decoded:
        if isinstance(part, bytes):                             #if a decoded part is encountered, then run decode() method using the given encoding
            msg_parts.append(part.decode(encoding or 'utf-8'))
        else:
            msg_parts.append(part)                              #if decoded part is not bytes type then append as it is
    return ''.join(msg_parts)                                   #returns the entire message as one string

""" HTML TYPE HANDLING """
def clean(text):
    return "".join(c if c.isalnum() else "_" for c in text)     #basically gets a folder name to store its webpage file in

def get_html(body, subject):
    folder_name = clean(subject)

    if not os.path.isdir("webpages"):                           #creates a webpages folder in cwd to store all the HTML type content from mails
        os.mkdir(f"webpages")
    if not os.path.isdir("webpages/" + folder_name):            #individual folders are created for the webpage of each mail
        os.mkdir("webpages/" + folder_name)
 
    filename = "index.html"
    filepath = os.path.join("webpages", folder_name, filename)

    with open(filepath, "w", encoding = "utf-8") as f:
        f.write(body)

    return filepath

""" PROGRAM OPTION FUNCTIONS """
def activate_emails():                                          #used to determine which email IDs get their mail fetched on execution
    while True:
        make_line_space(50)
        try:
            print("Choose emails to activate: ")
            for n, email in enumerate(mails):
                print (f'{n+1}:', email[0])
            choice = int(input("Choice (0 to Exit): "))
            print()
            if choice == 0:
                return
            
            mails[choice-1][4] = not mails[choice-1][4]
            is_active(mails[choice-1])
        except:
            print("\nInvalid choice, please select again")

def show_active_status():                                       #shows whether email IDs are getting their mail fetched or not
    for email in mails:
        print (f"{email[0]}: {email[4]}")
    print()

def is_active(email):
    if email[4]:
        print(f"{email[0]} is Active")
    else:
        print(f"{email[0]} is Not Active")
    print()
            
def change_search_criteria():                                   #used to change search criteria for each email ID or all at once
    search = input("Enter search string: ")
    while True:
        print("Choose email to change search criteria of (0 to Exit): ")
        for n, email in enumerate(mails):
            print (f'{n+1}:', email[0])
        choice = input("Choice: ")
        print()
        if choice == '0':
            return
        elif choice.lower() == 'all':
            for mail in mails:
                mail[5] = search
            print(f"Set all mails search criteria to {search}")
            return
        else:
            choice = int(choice)
            mails[choice-1][5] = search
            print(f"Set {mails[choice-1][0]} search criteria to {search}")

def show_search_criterias():
    for email in mails:
        print (f"{email[0]}: {email[5]}")
    print()

def change_number_of_mails():                                   #used to change how many mails will be fetched for each ID (max 30 due to connection limits from threads)
    while True:
        make_line_space(50)
        try:
            print("Choose email to change number of emails in (0 to Exit): ")
            for n, email in enumerate(mails):
                print (f'{n+1}:', email[0])
            choice = int(input("Choice (0 to Exit): "))
            print()
            if choice == 0:
                return
            
            current_mail = mails[choice-1]
            
            amount = int(input("How many mails to latest mails to fetch (max 30, min 1, 0 to Exit): "))
            print()
            if amount == 0:
                return
            elif amount < 0 or amount > 30:
                print("\nPlease choose a valid amount")

            else:
                current_mail[3] = amount
        except:
            print("\nInvalid choice, please select again")
            
def show_number_of_mails():
    for email in mails:
        print (f"{email[0]}: {email[3]}")
    print()

def handle_emails_after_fetch():                                #handles what to do with each fetched mail after fetching is done for each ID
    while True:
        try:
            make_line_space(50)
            print("Available mail ids to work on:")
            for i, email_id in enumerate(mails):
                print (f"{i+1:<2}: {email_id[0]}")

            choice = int(input("\nSelect id to work on (0 to Exit): "))
            if choice == 0:
                return
            elif choice < 0 or choice > len(mails):
                print("\nNo email exists")
                continue
            if not mails[choice-1][0] in fetched_mails:
                print("No mails for this email have been fetched yet")
                continue

            select_specific_email_for_id(mails[choice-1][0])
        except IndexError:
            print("\nInvalid choice, please select again 1")
        except ValueError:
            print("\nInvalid choice, please select again 2")

def select_specific_email_for_id(email_id):                     #accesses individual mail from pool of fetched mails
    while True:
        try:
            make_line_space(50)
            emails = fetched_mails[email_id]
            print ("\nAvailable emails to select: ")
            for i, email in enumerate(emails):
                print(f"{i+1:<2}: Subject: {email[1]}\n{'From':>8}: {email[0]}")

            choice = int(input("\nSelect email to view (0 to Exit): "))
            if choice == 0:
                return
            show_email_content(emails[choice-1])
        except IndexError:
            print("\nInvalid choice, please select again")
        except ValueError:
            print("\nInvalid choice, please select again")

def show_email_content(email):                                  #if content is plain text, print as it is, if it's HTML then opens up the webpage through index.html file
    make_line_space(50)                                         #that was created in the webpages folder in cwd
    if email[2].startswith("webpages"):
        webbrowser.open(email[2])
    else:
        print(email[2])

""" FETCHING MAILS """
#sets up imap server and fetches emails according to the executing thread
def fetch_group(start, finish, mail_store, creds, correction, num, thread = None):
    store = []                                                              #stores fetched emails locally before merging with main storage
    try:
        mail = setup_SSL_server(creds[2])                                   #sets up imap server with host specified in creds[2]
        authorise_creds(mail, creds)                                        #logs into the server
        select_folder(mail, 'INBOX')                                        #selects the folder to look for mails in
        result, data = search_folder(mail, search_criteria = creds[5])      #searches for specific mail in selected folder
    except:
        store.append("An error occurred, please make sure credentials and search criteria are correct")
        mail_store += store
        return

    mail_ids = data[0].split()                                              #gets individual mail ids in a list
    
    try:
        for i in range(start, finish, -1):                                  #start and finish of mail ids changes according to executing thread
            result, msg_data = mail.fetch(mail_ids[i], '(RFC822)')          #get the mail data from given mail id
            msg = email.message_from_bytes(msg_data[0][1])                  #convert to message from bytes
            subject = decode_header_value(msg['Subject'])
            _from = decode_header_value(msg['From'])

            if msg.is_multipart():                                          #if mail is multipart type then go through each part to handle them individually
                for part in msg.walk():
                    content_type = part.get_content_type()                  
                    content_disposition = str(part.get("Content-Disposition"))
                    try:
                        body = part.get_payload(decode=True).decode()       #get the body of this part
                    except:
                        pass
                    
                    if content_type == "text/html":                         #if type of content is HTML then gets the filepath to the index.html file for this content
                        body = get_html(body, subject)
            else:
                content_type = msg.get_content_type()                       #if mail is not multipart then just get body and check content type
                body = msg.get_payload(decode=True).decode()
                if content_type == "text/html":
                        body = get_html(body, subject)

            fetched_mails[creds[0]].append((_from, subject, body))          #stores this info for use after all mails are fetched like accessing individual mails
            
            store.append((_from, subject))

        if finish == -num + (correction - 1):                               #if last thread for this operation is executing
            for i in range(finish, finish - correction, -1):                #get the last few mails according to correction factor
                result, msg_data = mail.fetch(mail_ids[i], '(RFC822)')  
                msg = email.message_from_bytes(msg_data[0][1])
                subject = decode_header_value(msg['Subject'])
                _from = decode_header_value(msg['From'])
                
                if msg.is_multipart():                                      #does the same thing as above just for these last few mails on the last thread
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                        
                        if content_type == "text/html":
                            body = get_html(body, subject)
                        
                        elif content_type == "text/plain":
                            pass
                else:
                    content_type = msg.get_content_type()
                    body = msg.get_payload(decode=True).decode()
                    if content_type == "text/html":
                        body = get_html(body, subject)
                    elif content_type == "text/plain":
                        pass
                fetched_mails[creds[0]].append((_from, subject, body))
                
                store.append((_from, subject))
                
    except IndexError:
        store.append("No emails matching search criteria found")
    except:
        store.append("Some error occurred")

        
    mail.logout()                                                   #logout of server
    
    if thread != None:                                              #if executing thread is the first one then merge into main storage
        thread.join()                                               #else wait for the previous thread to finish
                                                                    #before merging mails into main storage
    mail_store += store

""" SETTING UP EMAIL THREADS """
#sets up all the threads required to fetch mails in groups
def get_mail(creds, num, thread = None):
    no_match = False
    setup_failure = False
    thread_amount, file_group, correction = get_thread_amount(num)  #gets required data to create the threads
    thread_list = {}                                                #stores created threads
    mail_store = []                                                 #main storage for fetched mails

    for n in range(1, thread_amount + 1):
        if n == 1:
            prev = None                                             #if first thread, then no need to wait for any previous threads
        else:
            prev = thread_list[n-1]                                 #subsequent threads wait for previous threads

        """
            args 1: -(file_group*(n-1))-1, gets the first mail id to fetch in the loop for this nth thread (starts with -1 for example to get latest mail)
            args 2: -(file_group*n)-1, gets the last mail id to fetch upto in the loop for this nth thread
        """
        thread_list[n] = threading.Thread(target = fetch_group, args = (-(file_group*(n-1))-1, -(file_group*n)-1, mail_store, creds, correction, num, prev))

    for t in thread_list:
        thread_list[t].start()                                      #starts all threads for fetch_group

    for t in thread_list:
        thread_list[t].join()                                       #waits for all threads to finish before moving on to printing mails

    if thread != None:                                              #all threads except the first will wait 
        thread.join()                                               #for previous threads to finish before printing
        
    print(f"Latest {num} emails for account: {creds[0]}: ")         #print out all mail in main storage 
    for i, m in enumerate(mail_store):                              #after all threads have finished executing
        if isinstance(m, tuple):
            print (f"{i+1:>2}: Subject: {m[1]}\n{'From':>8}: {m[0]}")
        else:
            if not no_match:
                print (m)
                no_match = True

    no_match = False
    print ()

""" MAIN """
def main():
    while True:
        try:
            make_line_space(50)
            print("MAIN MENU")
            print("1) Run program")
            print("2) Choose emails to activate")
            print("3) Show email active status")
            print("4) Change Search Criteria")
            print("5) Show email search criterias")
            print("6) Change amount of mails to fetch")
            print("7) Show amount of mails to be fetched by emails")
            print("8) Access fetched mails")
            print("Select 0 to Exit")
            choice = int(input("Choice: "))
            print()
            
            if choice == 1:
                email_threads = {}
                #creating threads for each email id, performant mail limit is like 100 for each email, gmail is messing up kinda
                n = 0
                for creds in mails:
                    if not creds[4]:
                        continue
                    if n == 0:
                        prev = None                                             #if first thread, then no need to wait for any previous threads
                    else:
                        prev = email_threads[n-1]                               #subsequent threads wait for previous threads
                    
                    email_threads[n] = threading.Thread(target = get_mail, args = (creds, creds[3], prev))
                    n += 1
                    fetched_mails[creds[0]] = []

                for t in email_threads:
                    email_threads[t].start()

                for t in email_threads:
                    email_threads[t].join()
            elif choice == 2:
                activate_emails()
            elif choice == 3:
                show_active_status()
            elif choice == 4:
                change_search_criteria()
            elif choice == 5:
                show_search_criterias()
            elif choice == 6:
                change_number_of_mails()
            elif choice == 7:
                show_number_of_mails()
            elif choice == 8:
                handle_emails_after_fetch()
            elif choice == 0:
                break
            else:
                print("Invalid choice, please select again")
        except:
            print("\nInvalid choice, please select again")
            
def make_line_space(n):
    print(f"\n{'-'*n}\n")

if __name__ == "__main__":
    main()
