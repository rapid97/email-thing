import threading
import time
import imaplib, email
from timeperf import TimePerf

#yahoo: imap.mail.yahoo.com
#gmail: imap.gmail.com

#email-id, app-password, mail-imap-server, no. of emails, whether to fetch for this email or not
mails = [["email-id", "app-password", "mail-imap-server", 30, True],
         ["email-id", "app-password", "mail-imap-server", 30, True],
         ["email-id", "app-password", "mail-imap-server", 30, True]]

def setup_SSL_server(server):
    server_timer = TimePerf(name = "server_setup")
    return imaplib.IMAP4_SSL(server)

def authorise_creds(mail, creds):
    cred_timer = TimePerf(name = f"{creds[0]} authorisation")
    mail.login(creds[0], creds[1])

def select_folder(mail, folder):
    folder_select_timer = TimePerf(name = "folder selection")
    mail.select(folder)

def search_folder(mail, search_criteria = 'ALL'):
    mail_searcher_timer = TimePerf(name = "mail searcher")
    return mail.search(None, search_criteria)

def data_to_list(data):
    split_timer = TimePerf(name = "list splitter")
    return data[0].split()

def create_search_string():
    print ("Select option to search for: ")

#returns the number of threads, no. of files for each thread and correction factor
#correction factor exists to get the correct number of files for even number of threads
def thread_groups(threads, num):
    return threads, int(num), int((num%1 * threads))

#gets the amount of threads to execute for file fetching
def get_thread_amount(num):
    n = 0
    while (num > 10):                                               #tries to make enough threads to keep time consumed around 10 seconds
        num = num/2
        n += 1

    return thread_groups(2**n, num)

#sets up imap server and fetches emails according to the executing thread
def fetch_group(start, finish, mail_store, creds, correction, num, thread = None):
    store = []                                                      #stores fetched emails locally before merging with main storage
    mail = setup_SSL_server(creds[2])                         #sets up imap server with host specified in creds[2]
    authorise_creds(mail, creds)                                  #logs into the server
    select_folder(mail, 'INBOX')                                            #selects the folder to look for mails in
    result, data = search_folder(mail, 'ALL')                         #searches for specific mail in selected folder
    mail_ids = data[0].split()                                      #gets individual mail ids in a list
 
    for i in range(start, finish, -1):                              #start and finish of mail ids changes according to executing thread
        result, msg_data = mail.fetch(mail_ids[i], '(RFC822)')      #get the mail data from given mail id
        #print (f"fetched mail for {creds[0]} with {thread}")
        msg = email.message_from_bytes(msg_data[0][1])              #convert to message from bytes
        store.append(msg['subject'])

    #print (finish, "+++", -num + correction)
    if finish == -num + (correction - 1):                           #if last thread for this operation is executing
        for i in range(finish, finish - correction, -1):            #get the last few mails according to correction factor
            result, msg_data = mail.fetch(mail_ids[i], '(RFC822)')  
            #print (f"fetched mail for {creds[0]} with {thread}")
            msg = email.message_from_bytes(msg_data[0][1])
            store.append(msg['subject'])
        
    mail.logout()                                                   #logout of server
    
    if thread != None:                                              #if executing thread is the first one then merge into main storage
        thread.join()                                               #else wait for the previous thread to finish
                                                                    #before merging mails into main storage
    mail_store += store
    
#sets up all the threads required to fetch mails in groups
def get_mail(creds, num, thread = None):
    #get_mail_timer = TimePerf(name = "get_mail_func")
    #get_mail_timer.startTick()
    thread_amount, file_group, correction = get_thread_amount(num)  #gets required data to create the threads
    thread_list = {}                                                #stores created threads
    mail_store = []                                                 #main storage for fetched mails

    #print ("thread:", thread_amount)
    for n in range(1, thread_amount + 1):
        #print (-(file_group*(n-1))-1, -(file_group*n)-1)
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
                                          
    #fetch_group(-1, -(num+1), mail_store, creds)

    if thread != None:                                              #all threads except the first will wait 
        thread.join()                                               #for previous threads to finish before printing
        
    print(f"Latest {num} emails for account: {creds[0]}: ")         #print out all mail in main storage 
    for i, m in enumerate(mail_store):                              #after all threads have finished executing
        print (i, m)
        
    #get_mail_timer.endTick()
    print ()
        
    #return mail_store

def show_active_status():
    for email in mails:
        print (f"{email[0]}: {email[4]}")
    print()
        
def is_active(email):
    if email[4]:
        print(f"{email[0]} is Active")
    else:
        print(f"{email[0]} is Not Active")
    print()
    
def activate_emails():
    while True:
        print("Choose emails to activate: ")
        for n, email in enumerate(mails):
            print (f'{n+1}:', email[0])
        choice = int(input("Choice: "))
        print()
        if choice == 0:
            return
        
        mails[choice-1][4] = not mails[choice-1][4]
        is_active(mails[choice-1])

def main():
    main_timer = TimePerf(name = "Main", auto = True)
    run_timer = TimePerf(name = "run")
    while True:
        print("MAIN MENU")
        print("1) Choose emails to activate")
        print("2) Run program")
        print("3) Show email active status")
        choice = int(input("Choice: "))
        print()
        
        if choice == 1:
            activate_emails()
        elif choice == 2:
            run_timer.startTick()
            email_threads = {}
            #creating threads for each email id, performant mail limit is like 100 for each email, gmail is messing up kinda
            n = 0
            for creds in mails:
                #print (-(file_group*(n-1))-1, -(file_group*n)-1)
                if not creds[4]:
                    continue
                if n == 0:
                    prev = None                                             #if first thread, then no need to wait for any previous threads
                else:
                    prev = email_threads[n-1]                               #subsequent threads wait for previous threads

                email_threads[n] = threading.Thread(target = get_mail, args = (creds, creds[3], prev))
                n += 1

            for t in email_threads:
                email_threads[t].start()

            for t in email_threads:
                email_threads[t].join()

            run_timer.endTick(clear_start_time = False)
            #show_mail(mails[0], 15)
        elif choice == 3:
            show_active_status()
        elif choice == 0:
            break

if __name__ == "__main__":
    main()

