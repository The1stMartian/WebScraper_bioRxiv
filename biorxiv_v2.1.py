from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv
import re
import time
import pandas as pd
import numpy as np

###################################################################################################################
def load_previous_data(infile):
        '''
        - Loads previously recorded data
        - Useful is the web scraping was shut down before completing
        - Script can be restarted at the last link
        - if No previous data being used, infile = NA
        '''
        # Dictionary for converting extracted last subject name over the URL-formatted subject name
        subject_names = {"Developmental Biology":"developmental-biology", "Ecology":"ecology","Epidemiology":"epidemiology",
        "Evolutionary Biology":"evolutionary-biology","Genetics":"genetics","Genomics":"genomics","Immunology":"immunology",
        "Microbiology":"microbiology","Molecular Biology":"molecular-biology","Neuroscience":"neuroscience",
        "Paleontology":"paleontology","Pathology":"pathology","Pharmacology and Toxicology":"pharmacology-and-toxicology",
        "Physiology":"physiology","Plant Biology":"plant-biology", "Scientific Communication and Education":"scientific-communication-and-education",
        "Synthetic Biology":"synthetic-biology","Systems Biology":"systems-biology","Zoology":"zoology",
        "Animal Behavior and Cognition":"animal-behavior-and-cognition","Biochemistry":"biochemistry", 
        "Bioengineering":"bioengineering", "Bioinformatics":"bioinformatics", "Biophysics":"biophysics", 
        "Cancer Biology":"cancer-biology","Cell Biology":"cell-biology", "Clinical Trials":"clinical-trials"}

        if infile == "NA":
                return   "NA","NA","NA", "NA","NA", "NA"
        else:  
                infileDF = pd.read_csv(infile)
                lastPage = infileDF["pageNumber"].iloc[-1]
                lastLink = infileDF["links"].iloc[-1]
                lastSub_raw = infileDF["subject"].iloc[-1]
                lastPaperTitle = infileDF["title"].iloc[-1]
                lastSub = subject_names[lastSub_raw]
                allRecordedSubs = infileDF["subject"].unique()
                previousLinks = infileDF["links"]
                
                # All fully-completed subjects/topics
                allRecordedSubs = np.delete(allRecordedSubs,np.where(allRecordedSubs == lastSub_raw))
                print("ARS: ", allRecordedSubs)
                
                # Change formatting on completed subjets/topics
                completeSubs = []
                for sub in allRecordedSubs:
                    completeSubs.append(subject_names[sub])
                print()
                print("#"*50)
                print("### Web scraper starting...")
                print("#"*50)
                print()
                print()
                print("#"*50)
                print("### Skipping previously collected data in: ", infile.split("/")[-1])
                print("#"*50)
                print()
                print("#"*50)
                print("### Ignoring previously recorded topics:")
                for tpc in completeSubs:
                    print("   ", tpc)
                print("#"*50)
                print()
                print("#"*50)
                print("### Last recorded paper was: ", lastPaperTitle)
                print("#"*50)
                print()
                return completeSubs, lastSub, lastPage, lastLink, lastPaperTitle, previousLinks

###################################################################################################################
def record(url_list, missed_list, current_data, recursion_count, max_recursion, driver, pageNumber):
        '''
        - current_data is a list of dictionaries
        - each dictionary is one manuscript's data
        - Recursively follow urls in url list (1 page of urls)
        - Record data, or determine that link/paper is an erroneous entry
        - Keep trying until max recursion depth is met
        - V2.0: also removes previosly loaded data (if desired)
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
                                url_list.remove(m)
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
                                        paper_data['pageNumber'] = pageNumber
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
                        return record(url_list, missed_list, current_data, recursion_count+1, max_recursion, driver, pageNumber)

###################################################################################################################
def scrape(topics, wd, completedTopicsList, lastTopic1, lastLinksPage1, lastLink1, ptitle, recordedLinks):
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
    header = "first_author,last_author,subject,title,year,month,pdfDownloads,fullText,abstractViews,tweets,links,pageNumber\n"
    csv_file.write(header)

    max_attempts = 6

    ####################################################################################################
    # If loading/skipping previously recorded data (due to partially-completed scraping session)
    # Removes completed and partially completed topics from the list
    # Then adds the most recent topic back to the list in position 1
    # pageNumber == starting point
    ####################################################################################################               
    # If there's an entry for lastTopic1, it indicates that previous data is being added to, not starting from zero
    # Therefore, remove pre-recorded subjects/topics from download list
    if lastTopic1 != "NA":
        try:
            for c in completedTopicsList:
                topics.remove(c)
            
            # Also remove final topic that was interrupted, then add it back to the beginning of the list
            topics.remove(lastTopic1)
            topics.insert(0,lastTopic1)

        except ValueError:
            print("ERROR: couldn't find last topic for removal from desired topics list:", c)
            print("Topics list: ", topics)

    # Starting at either the first topic in the list, or the most recent topic previously recorded
    for topic in topics:

        # Missed links are recorded at the end of every topic
        missedLinkList = []
        
        startPage = 0
        
        # Start data collection at links page 0, or links page = most recent page
        # Also wait until the previous link has been found, then start collecting data ("lastLinkFound" variable defaults to
        #     "yes" for the standard condition of starting from zero, allowing data collection to start immediately
        # Otherwise just keep moving forward
        lastLinkFound = "yes"
        if topic == lastTopic1:
            startPage = int(lastLinksPage1)
            lastLinkFound = "no"
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
        print()
        print("#"*50)
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        print("##### Beginning data collection...")
        print("##### Start Time: ", str(t.tm_hour)+":"+str(t.tm_min)+":"+str(t.tm_sec))
        print("##### Topic: ", topic)
        print("##### Starting at page: ", startPage)
        print("##### Total pages of Links: ", lastPageNumber)
        print("#"*50)
        print()

        for i in range(startPage, lastPageNumber):  # should be range(lastPageNumber)
            # Manuscript data is recorded at the end of every page of links
            ListOfDictionaries = {}

            # First page of manuscript links --> gets total pages of links
            print("##### Current Page: ",i, "out of", lastPageNumber)

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
            # If appropriate, first remove all links that were previously recorded.
            if lastLinkFound == "no":

                # The last recorded link (lastLink1) should be on the first page of results (links)
                if recordedLinks.str.contains(lastLink1).sum() >0:
                    print()
                    print("#"*50)
                    print("Last recorded link successfully identified in current page of links.")
                    print("That means the data acquisition should pick up right where the script left off.")
                    print("Continuing...")
                    print("#"*50)
                    print()
                    lastLinkFound = "yes"
                
                # If it's not there, exit the program - user should find the problem
                elif lastLink1 not in links:
                    print()
                    print("#"*50)
                    print("Error: last link not found in first page of results links.")
                    print("Exiting. Something is wrong.")
                    print("Page Number: ", i)
                    print("Next desired link: ", lastLink1)
                    print("Links pre-deletion: ", links)
                    print("Links post-deletion", links_edited)
                    print("EXITING.")
                    print("#"*50)
                    exit()

                # Remove links from this first results page if they were already recorded
                for i in links:
                    if recordedLinks.str.contains(i).sum() >0:
                        links.remove(i)

                print()
                print("#"*50)
                print("The number of links kept from the first page is: ", len(links), "out of", numberLinksOnPage)
                print("#"*50)
                print()
                numberLinksOnPage = len(links)
            
            # All loops will be directed here after the first pre-recorded link is found 
            if lastLinkFound == "yes":
                missedLinkList, ListOfDictionaries = record(links, [], [], 0, max_attempts, wd, i)

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
            print(r"### Links followed: "+ str(totalLinksFollowed) + " (" + str(round(ratio,2)) + "% Success)")
                

        ### End of topic ###
        # Write missing links for this topic and blank memory
        for missingLink in missedLinkList:
                ml_file.write(missingLink + "," + topic + "," + "\n")

###################################################################################################################
# Customize
###################################################################################################################
# If not loading previous data, set previousDataFile to "NA" 
# This will set the script to download all bioRxiv data
# Opening previous data will allow the script to skip previously acquired data
#previousDataFile = "C:/Users/chris/OneDrive/OneDrive/DataAnalysis/Projects/selenium_project/Keep_Data123_cleaned.csv"
previousDataFile = "NA"
completeTopics, lastTopic, lastURLPage, lastURL, lastTitle, prevLinks = load_previous_data(previousDataFile)

# Selenium webdriver location
WEBDRIVER = webdriver.Chrome(executable_path=r'<full file path>')
WEBDRIVER.implicitly_wait(1.5)

# Customize subjects list if only a subset are desired
subjects = subjects = ["animal-behavior-and-cognition","biochemistry", "bioengineering", "bioinformatics", "biophysics", "cancer-biology",
        "cell-biology", "clinical-trials", "developmental-biology", "ecology", "epidemiology","evolutionary-biology","genetics",
        "genomics","immunology","microbiology","molecular-biology","neuroscience","paleontology","pathology","pharmacology-and-toxicology",
        "physiology","plant-biology","scientific-communication-and-education","synthetic-biology","systems-biology","zoology"]
###################################################################################################################
scrape(subjects, WEBDRIVER, completeTopics, lastTopic, lastURLPage, lastURL, lastTitle, prevLinks)
WEBDRIVER.close()
exit()