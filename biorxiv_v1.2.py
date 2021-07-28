from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv
import re
import time
csv_file = open('bioRxivData.csv', 'w', encoding='utf-8', newline='')
writer = csv.writer(csv_file)
header = "first_author,last_author,subject,title,year,month,pdfDownloads,fullText,abstractViews,tweets\n"
csv_file.write(header)

driver = webdriver.Chrome(executable_path=r'C:/Users/chris/OneDrive/OneDrive/DataAnalysis/python/Selenium/chromedriver.exe')
driver.implicitly_wait(0.5)

topics = ["biochemistry", "bioengineering", "bioinformatics", "biophysics", "cancer-biology",
        "cell-biology", "clinical-trials", "developmental-biology", "ecology", "epidemiology","evolutionary-biology","genetics",
        "genomics","immunology","microbiology","molecular-biology","neuroscience","paleontology","pathology","pharmacology-and-toxicology",
        "physiology","plant-biology","scientific-communication-and-education","synthetic-biology","systems-biology","zoology", "animal-behavior-and-cognition"]

for topic in topics:
        topic_link = 'https://www.biorxiv.org/collection/' + topic
        
        
        # Get all pages of search results (page links)
        driver.get(topic_link)
        lastPageNumber = int(driver.find_element_by_xpath('//*[@class="pager-last last odd"]').text)
        total_links = 0
        print("##### Topic: ", topic)
        print("##### Pages of Links: ", lastPageNumber)
        
        for i in range(lastPageNumber):  # should be range(lastPageNumber)
                # First page of manuscript links --> gets total pages of links
                links = []
                newlink = "https://www.biorxiv.org/collection/" + topic + "?page=" + str(i)
                
                # Get 1 page of links (up to total)
                driver.get(newlink)
                rawLinks = driver.find_elements_by_xpath('.//*[@class="highwire-cite-title"]//a')
                for a in rawLinks:
                        try:
                                links.append(a.get_attribute('href'))
                        except StaleElementReferenceException:
                                continue
                linksOnPage = len(links)
                total_links += linksOnPage
                #print("### Topic Page: ", topic, ":", i)
                print("### Papers recorded: ", total_links)

                # For each results page (10 paper links), go through each paper, record data for each, then go on to the next page of links
                for link in links:
                        out_data = {}
                        fullLink = link + ".article-metrics"
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
                                out_data['firstAuthor'] = firstAuthor
                                out_data['lastAuthor'] = lastAuthor
                                out_data['subject'] = subject
                                out_data['title'] = title
                                out_data['year'] = year
                                out_data['month'] = month
                                out_data['pdfDownloads'] = PDF
                                out_data['fullText'] = fullText
                                out_data['abstractViews'] = abstract
                                out_data['tweets'] = tweets
                                writer.writerow(out_data.values())
                        
                        # Some papers have no author, or lack some other field. Move past these.
                        except NoSuchElementException as exception:
                                print("Error at link: ", fullLink)
                                print(exception)

csv_file.close()
driver.close()