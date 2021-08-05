# bioRxiv_scraper
Python-selenium web scraper for bioRxiv publication data

The bioRxiv scraper will collect data on every manuscript in the bioRxiv database using Selenium. Data include author and title information, the number of views by type, and the number of Tweets a paper has received. Additional scraping features could certainly be added including other social media mentions. 
Version 1.4: changed to Chrome headless mode for better performance

Version 1.9: Major updates
- headless doesn't run properly so the headed browser is being used
- changed formatting to make better use of functions
- implemented recursive page downloading for missed pages as the previous version frequently missed pages. This seems to be due to slow download speeds triggering an error and the pages were simply skipped. The recursive function allows for several successive attempts before the page is abandoned.
- All links are now recorded as an outfile
- Links to all missing papers are now recorded as an outfile
- The links files will provide users with the opportunity to avoid re-downloading old manuscript data
- A (future) scraper script should be able to download only new papers by avoiding the old links