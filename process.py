import os
import time
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import pymongo
from unidecode import unidecode

def parser(company_name):

    url_company = 'https://www.linkedin.com/search/results/index/?keywords='
    all_names=[]
    try:
        company_name = company_name.rstrip().replace(' ','+')
        option = webdriver.ChromeOptions()
        option.add_argument(" — incognito")
        browser = webdriver.Chrome(executable_path=os.path.abspath('chromedriver'), chrome_options=option)
        browser.get('https://www.linkedin.com')
        browser.find_element_by_class_name('login-email').send_keys("careers@newgenapps.com")
        browser.find_element_by_class_name('login-password').send_keys("C@r33r$NG@")
        browser.find_element_by_id('login-submit').click()
        browser.get(url_company+company_name)
        next=True
        n=0
        while next and n<=2:
            n+=1
            print('page '+str(n))
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            html = browser.page_source
            soup = bs(html, 'lxml')
            wrappers = soup.find_all('div',class_='search-result__wrapper')
            for candy in wrappers:
                if candy.find_all('span',class_='name'):
                    all_names.append((candy.find_all('span',class_='name')[0].text,candy.find_all('p',class_='subline-level-1')[0].text.strip().encode('ascii', 'ignore').decode('utf-8')))
                else:
                    pass
            if soup.find('button',class_='next'):
                browser.find_element_by_class_name('next').click()
            else:
                next=False
    except Exception as e:
        print(e)
    try:
        browser.quit()
    except Exception as e:
        print(e)
    return all_names


def savenames():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["sales_automation_development"]
    orgs = mydb["hubspot_organisations"]
    orgmails = mydb["hubspot_organisations_people"]
    i = 0
    j = 0
    n=orgs.find().count()
    a = 50
    na = n//a + 1
    for value in range(na):
        for org in orgs.find()[value * a:value * a + a]:
            try:
                j=j+1
                print(j)
                company = org['name']
                domain = org['domain']
                hubspot_org_id = org['_id']
                all_names = parser(company)
                persons = []
                if all_names:
                    for data in all_names:
                        name = data[0]
                        designation = data[1]
                        fname,lname = getnames(name)
                        emails = getpatterns(fname,lname,domain)
                        persons.append({'name':name,
                                        'designation':designation,
                                        'emails':emails})
                    mydict = {"hubspot_org_id":hubspot_org_id,
                            "company_name": company,
                            "domain":domain,
                            "persons":persons}
                    x = orgmails.insert_one(mydict)
                    print(x)
                    i=i+1
                    print(i)
            except Exception as e:
                print(e)

def getnames(name):
    try:
        name = unidecode(name).lower()
        name = name.split()
        newnamelist = []
        newname=''
        for word in name:
            if '.' not in word and '(' not in word and ';' not in word and len(word.strip())>1 :
                newnamelist.append(word)
        for value in newnamelist:
            newname = newname + ' ' + value
        ignrlst = ['Dr.','Mr.','Ms.','llb','&','marketing','healthcare',
                    'maicd','bsc','mca','msc','fcpa','fcga',',','fcsi','cfa','cpa']
        for a in ignrlst:
            newname = newname.replace(a.lower(),'')
        fname=newname.split()[0]
        lname=newname.split()[1]
        return(fname,lname)
    except Exception as e:
        print(e)

def getpatterns(fname,lname,domain):
    try:
        first=fname.lower()
        last=lname.lower()
        user_patterns = [ first+last,
                        last+first,
                        first+'.'+last,
                        last+'.'+first,
                        first+'_'+last,
                        last+'_'+first,
                        first[0]+last,
                        last[0]+first,
                        first+last[0],
                        last+first[0],
                        first[0]+'.'+last,
                        last[0]+'.'+first,
                        first[:3]+last[:2],
                        last[:3]+first[:2],
                        last+first[:3],
                        first+last[:3] ]

        email_patterns= []
        for patn in user_patterns:
            email_patterns.append(patn+'@'+domain)
        return email_patterns
    except Exception as e:
        print(e)

if __name__ == '__main__':
    savenames()
