from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv
import re
import time
###################################################################################################################
def record(url_list, missed_list, current_data, recursion_count, max_recursion, driver):
        '''
        - current_data is a list of dictionaries
        - each dictionary is one manuscript's data
        - Recursively follow urls in url list (1 page of urls)
        - Record data, or determine that link/paper is an erroneous entry
        - Keep trying until max recursion depth is met
        '''

        #print("RECORD FUNCTION CALLED")
        #print("url list: ", url_list)
        #print("missing_list: ", missed_list)
        #print("current_data len: ", len(current_data))
        #print("recursion count: ", recursion_count)
        
        # All links successfully followed if the url_list is empty - return data.
        remaining_URLs = len(url_list)
        if remaining_URLs == 0:
                return missed_list, current_data

        else:
                # Recursively call the function, trying URLs until Max recursion reached or all URLs were successfully recorded
                # If max recusion met and some URLs (papers/data points) were not recorded: remaining urls > "missed" list
                if recursion_count >= max_recursion:
                        for m in url_list:
                                missed_list.append(m)
                                url_list.remomve(m)
                        return current_data
                        #record([], missed_list, current_data, max_recursion)
                
                # Max recursion not met, keep trying
                else:
                        for url in url_list:
                                paper_data = {}
                                fullLink = url + ".article-metrics"
                                #print("Trying Link: ", fullLink)
                                driver.get(fullLink)

                                # Try to get views
                                try:
                                        allViewsRaw = driver.find_element_by_xpath('//*[@class="cshl_total"]').text
                                        tsp = allViewsRaw.split(" ")
                                        abstract = tsp[-3]
                                        fullText = tsp[-2]
                                        PDF = tsp[-1]
                                except NoSuchElementException as exception:
                                        abstract = str(0)
                                        fullText = str(0)
                                        PDF = str(0)

                                # Try to get tweets
                                try:
                                        pretweet = driver.find_element_by_xpath('//*[@style="padding-left: 10px; line-height:18px; border-left: 16px solid #74CFED;"]').text
                                        tweets = pretweet.split(" ")[-1]
                                except NoSuchElementException as exception:
                                        tweets = str(0)

                                try:
                                        # These should all work!
                                        title = driver.find_element_by_xpath('//*[@class="highwire-cite-title"]').text
                                        surnames2 = driver.find_element_by_xpath('//*[@class="highwire-cite-authors"]').text
                                        authorlist = []
                                        for i in surnames2.split(","):
                                                author = ""
                                                authorSplit = i.split()
                                                for j in authorSplit:
                                                        if j not in ["ORCID", "View", "Profile"]:
                                                                author = author + " " + j
                                                auth_check = author.replace(" ", "")
                                                if auth_check != "":
                                                        authorlist.append(author[1:])
                                        firstAuthor = authorlist[0]
                                        lastAuthor = authorlist[-1]
                                        subject = driver.find_element_by_xpath('//*[@class="highwire-article-collection-term"]').text
                                        
                                        # Collect date
                                        posted = (driver.find_element_by_xpath('//*[@class="panel-panel panel-region-sidebar-right"]').text).split("\n")[2].split(" ")
                                        year = posted[3][:-1]
                                        month = posted[1]
                                        day = posted[2][:-1]

                                        # Record data
                                        paper_data['firstAuthor'] = firstAuthor
                                        paper_data['lastAuthor'] = lastAuthor
                                        paper_data['subject'] = subject
                                        paper_data['title'] = title
                                        paper_data['year'] = year
                                        paper_data['month'] = month
                                        paper_data['pdfDownloads'] = PDF
                                        paper_data['fullText'] = fullText
                                        paper_data['abstractViews'] = abstract
                                        paper_data['tweets'] = tweets
                                        paper_data['link'] = url
                                        current_data.append(paper_data)
                                        url_list.remove(url)

                                ### End of individual link ###
                                # Some papers have no author, or lack some other field. Move past these.
                                except NoSuchElementException as exception:
                                        print("Error at link: ", fullLink)
                                        #print(exception)
                                        url_list.remove(url)
                                        missed_list.append(url)

                        # Recursive call with updated data.
                        return record(url_list, missed_list, current_data, recursion_count+1, max_recursion, driver)

###################################################################################################################
def scrape(topics, wd):
    '''
    - Main function
    '''

    # Data will be recorded here
    csv_file = open('bioRxivData.csv', 'w', encoding='utf-8', newline='')

    # All manuscript links will be recorded here so that you don't need to scrape the whole website again next time
    all_file = open('all_links.csv', 'w', encoding='utf-8', newline='')
    all_file.write("link,topic\n")

    # The links to missed papers will be recorded here
    ml_file = open('missed_papers.csv', "w", encoding='utf-8', newline='')
    ml_file.write("link, topic\n")

    writer = csv.writer(csv_file)
    header = "first_author,last_author,subject,title,year,month,pdfDownloads,fullText,abstractViews,tweets,links\n"
    csv_file.write(header)

    max_attempts = 6
    for topic in topics:
        totalLinksFollowed = 0
        totalLinksRecorded = 0
        totalLinksMissed = 0

        topic_link = 'https://www.biorxiv.org/collection/' + topic
        
        # Get all pages of search results (page links)
        wd.get(topic_link)
        lastPageNumber = int(wd.find_element_by_xpath('//*[@class="pager-last last odd"]').text)
        totalLinks = 0

        # Records the links of all manuscripts that were/not downloaded
        missed_links = []
        
        # Report on time/status of the script
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        print("##### Time: ", str(t.tm_hour)+":"+str(t.tm_min)+":"+str(t.tm_sec))
        print("##### Topic: ", topic)
        print("##### Pages of Links: ", lastPageNumber)
        
        for i in range(lastPageNumber):  # should be range(lastPageNumber)
                # First page of manuscript links --> gets total pages of links
                print("##### Page: ",i, "out of", lastPageNumber)

                # Every paper link on the current page
                links = []
                foundOnPage = len(links)
                newlink = "https://www.biorxiv.org/collection/" + topic + "?page=" + str(i)
                
                # Get 1 page of links (up to total)
                wd.get(newlink)
                rawLinks = wd.find_elements_by_xpath('.//*[@class="highwire-cite-title"]//a')
                for a in rawLinks:
                        try:
                                links.append(a.get_attribute('href'))
                        except StaleElementReferenceException:
                                continue
                
                # Record all links
                for j in links:
                        all_file.write(j +","+ topic + "\n")
                numberLinksOnPage = len(links)
                
                # For each results page (10 paper links), Record Data
                missedLinkList, ListOfDictionaries = record(links, [], [], 0, max_attempts, wd)

                # Record data
                for pageData in ListOfDictionaries:
                        writer.writerow(pageData.values())
                
                # Append missed links to list for whole topic
                number_missed = 0
                for missed in missedLinkList:
                        missed_links.append(missed)
                number_missed = len(missedLinkList)

                # Report on percent recorded:
                number_recorded = len(ListOfDictionaries)
                totalLinksMissed += number_missed
                totalLinksRecorded += number_recorded
                totalLinksFollowed += numberLinksOnPage

                ratio = (float(totalLinksRecorded)/totalLinksFollowed)*100
                print(r"### Links followed: "+str(totalLinksFollowed) + " (" + str(ratio) + "% Success)")
                

        ### End of topic ###
        # Write missing links for this topic and blank memory
        for missingLink in missedLinkList:
                ml_file.write(missingLink + "," + topic + "," + "\n")

###################################################################################################################
WEBDRIVER = webdriver.Chrome(executable_path=r'C:/Users/chris/OneDrive/OneDrive/DataAnalysis/python/Selenium/chromedriver.exe')
WEBDRIVER.implicitly_wait(1.5)
subjects = ["developmental-biology", "ecology", "epidemiology","evolutionary-biology","genetics",
        "genomics","immunology","microbiology","molecular-biology","neuroscience","paleontology","pathology","pharmacology-and-toxicology",
        "physiology","plant-biology","scientific-communication-and-education","synthetic-biology","systems-biology","zoology",
        "animal-behavior-and-cognition","biochemistry", "bioengineering", "bioinformatics", "biophysics", "cancer-biology",
        "cell-biology", "clinical-trials"]
scrape(subjects, WEBDRIVER)
csv_file.close()
WEBDRIVER.close()