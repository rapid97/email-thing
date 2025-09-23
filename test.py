import threading
import time
import imaplib, email

mails = [("email id", "app password", "mail imap server"),
         ("email id", "app password", "mail imap server"),
         ("email id", "app password", "mail imap server")]

#returns the number of threads, no. of files for each thread and correction factor
#correction factor exists to get the correct number of files for even number of threads
def thread_groups(threads, num):
    return threads, int(num), int((num%1 * threads))

#gets the amount of threads to execute for file fetching
def get_thread_amount(num):
    n = 0
    while (num > 10): #tries to make enough threads to keep time consumed around 10 seconds
        num = num/2
        n += 1

    return thread_groups(2**n, num)

#sets up imap server and fetches emails according to the executing thread
def fetch_group(start, finish, mail_store, creds, correction, num, thread = None):
    store = []                                                      #stores fetched emails locally before merging with main storage
    mail = imaplib.IMAP4_SSL(creds[2])                              #sets up imap server with host specified in creds[2]
    mail.login(creds[0], creds[1])                                  #logs into the server
    mail.select("INBOX")                                            #selects the folder to look for mails in
    result, data = mail.search(None, "ALL")                         #searches for specific mail in selected folder
    mail_ids = data[0].split()                                      #gets individual mail ids in a list
    for i in range(start, finish, -1):                              #start and finish of mail ids changes according to executing thread
        result, msg_data = mail.fetch(mail_ids[i], "(RFC822)")      #get the mail data from given mail id
        #print (f"fetched mail for {creds[0]} with {thread}")
        msg = email.message_from_bytes(msg_data[0][1])              #convert to message from bytes
        store.append(msg["subject"])

    #print (finish, "+++", -num + correction)
    if finish == -num + (correction - 1):                           #if last thread for this operation is executing
        for i in range(finish, finish - correction, -1):            #get the last few mails according to correction factor
            result, msg_data = mail.fetch(mail_ids[i], "(RFC822)")  
            #print (f"fetched mail for {creds[0]} with {thread}")
            msg = email.message_from_bytes(msg_data[0][1])
            store.append(msg["subject"])
        
    mail.logout()                                                   #logout of server
    
    if thread != None:                                              #if executing thread is the first one then merge into main storage
        thread.join()                                               #else wait for the previous thread to finish
                                                                    #before merging mails into main storage
    mail_store += store
    
#sets up all the threads required to fetch mails in groups
def get_mail(creds, num, thread = None):
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
    for i, m in enumerate(mail_store):                                            #after all threads have finished executing
        print (i, m)
    print ()
        
    #return mail_store

def main():
    #creating threads for each email id, performant mail limit is like 100 for each email, gmail is messing up kinda
    t1 = threading.Thread(target = get_mail, args = (mails[0], 50, None))
    t2 = threading.Thread(target = get_mail, args = (mails[1], 50, t1))
    t3 = threading.Thread(target = get_mail, args = (mails[2], 50, t2))

    #start all email threads
    t1.start()
    t2.start()
    #t3.start()

    #main does not finish till all email threads finish
    t1.join()
    t2.join()
    #t3.join()

    #show_mail(mails[0], 15)


if __name__ == "__main__":
    time_start = time.perf_counter()
    main()
    elapsed = time.perf_counter() - time_start
    print (f"Took {elapsed} seconds")


