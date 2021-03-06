#!/usr/bin/env python
import os, sys, time, re
import plistlib
import requests
from BeautifulSoup import BeautifulSoup
import simplejson as json
import boto
import os

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

bucket_name = AWS_ACCESS_KEY_ID.lower() + '-amul-bucket'
conn = boto.connect_s3(AWS_ACCESS_KEY_ID,
	    AWS_SECRET_ACCESS_KEY)

def create_s3_bucket(bucket_name):
	try:
		bucket = conn.create_bucket(bucket_name, location=boto.s3.connection.Location.APSoutheast)
		return bucket
	except boto.exception.S3CreateError as e:
		print 'Unable to create bucket %s' % e
	return None

def get_s3_bucket(bucket_name):
	bucket = conn.get_bucket(bucket_name)
	return bucket

def percent_cb(complete, total):
    sys.stdout.write('.')
    sys.stdout.flush()

#bucket = create_s3_bucket(bucket_name)
bucket = get_s3_bucket(bucket_name)
json_key = bucket.get_key('amul.json')
plist_key = bucket.get_key('amul.plist')

def request(url):
	headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.6) Gecko/20040113'}
	return requests.get(url,headers=headers).content

next_marker = 'Next 10 Records'

def main():
    main_html = request('http://amul.com/m/amul-hits')
    soup = BeautifulSoup(main_html)
    year_links = soup.findAll('a', text=re.compile(r'Amul hits of the year'))
    #print scrape_year(year_links[0])
    output = json.dumps([scrape_year(year) for year in year_links])
    json_key.set_contents_from_string(output,cb=percent_cb,num_cb=25)
    json_key.set_acl('public-read')

def scrape_year(year):
    year = year.strip('Amul hits of the year')
    year_obj=[]
    count = 0
    while(True):
        page = request('http://amul.com/m/amul-hits?s=%s&l=%s' % (year, str(count)))
        year_obj.extend(scrape_page(page))
        count = count + 1
        if next_marker not in page:
            break
    return dict(year=year, topicals=year_obj)

def scrape_page(page):
	page_obj = []
	soup = BeautifulSoup(page)
	main_table = soup.findAll('table')[1]
	temp1 = main_table.findAll('tr')
	for tr in temp1:
		temp2 = tr.findAll('img')
		for link in temp2:
			try:
				obj = dict(src=link['src'].encode('utf-8'), alt=link['alt'].encode('utf-8'), title=link['title'].encode('utf-8'))
				page_obj.append(obj)
			except:
				pass
	return page_obj

if __name__ == "__main__":
    main()	
