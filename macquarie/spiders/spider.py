import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import MmacquarieItem
from itemloaders.processors import TakeFirst
import json

pattern = r'(\xa0)?'
base = 'https://www.macquarie.com/api/search?c=macq:press-releases&size=20&currentUrl=/uk/en/about/news/releases.html&co=uk&la=en&t=mac-common%3Aregion%2Faustralia-and-new-zealand&from={}'

class MmacquarieSpider(scrapy.Spider):
	name = 'macquarie'
	page = 0
	start_urls = [base.format(page)]

	def parse(self, response):
		data = json.loads(response.text)
		for index in range(len(data['hits'])):
			link = data['hits'][index]['_source']['target-url']
			yield response.follow(link, self.parse_post)

		if data['hits']:
			self.page += 20
			yield response.follow(base.format(self.page), self.parse)

	def parse_post(self, response):
		try:
			date = response.xpath('//div[contains(@class,"date ")]/p/text()').get().strip()
		except AttributeError:
			date = response.xpath('//div[@class="cmp-text"]/p/text()').get().strip()

		date = re.findall(r'\d+\s\w+\s\d+', date)
		title = response.xpath('//h1/text()').get()
		content = response.xpath('(//div[@class="dark-text"]/div[@class="cmp-text"])[position()<last()]//text()').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=MmacquarieItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
