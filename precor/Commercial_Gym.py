import scrapy
from ..items import Manual

class PrecorComSpider(scrapy.Spider):
    name = 'precor.com'
    start_urls = [
        'https://help.precor.com/global/Content/Home.htm'
    ]

    def parse(self, response):
        for url in response.css("p a::attr(href)").getall():
            product = response.css("p a::text").get().strip()
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse_product, meta={'product': product})

    def parse_product(self, response):
        subcategory_urls = response.css('.tile-title a::attr(href)').getall()

        if subcategory_urls:
            # If there are subcategory URLs, follow them using parse_listing
            for url in subcategory_urls:
                yield response.follow(url=response.urljoin(url), callback=self.parse_listing, meta=response.meta)
        else:
            # If no subcategories, directly parse the items
            yield from self.parse_item(response)
    def parse_listing(self, response):
        for url in response.css('.home-tiles-container a::attr(href)').getall():
            yield response.follow(url=response.urljoin(url), callback=self.parse_item, meta=response.meta)

    def parse_item(self, response):

        # Product
        product = response.xpath('//html/@data-mc-toc-path').get(default='').strip()
        product_parts = product.split('|')
        if len(product_parts) > 1:
            product = product_parts[1].strip()



        # Iterate over each PDF link in the table
        for item in response.css('table.TableStyle-Lang_table tr.TableStyle-Lang_table-Body-Body1'):
            commercial_gym = Manual()

            # Extracting the file URL as a list (required by Scrapy for `file_urls`)
            commercial_gym['file_urls'] = [item.css('td a::attr(href)').get()]

            # Extracting the document type, only if it's a "Getting Started Guide"
            type_doc = response.css('h2::text').getall()



            product_lang = item.css('td a::attr(title)').get()
            if product_lang:
                parts = product_lang.split('/')
                if len(parts) > 1:
                    first_part, second_part = parts[0].strip(), parts[1].strip()
                    if second_part.lower() == "french"  :
                        product_lang = second_part
                    else:
                        product_lang = first_part
                else:
                    product_lang = parts[0].strip()
            else:
                product_lang = "English"

            # if len(type_doc) > 1 and "Getting Started Guide" in type_doc[1].lower():
            #     commercial_gym['type_doc'] = "Getting Started Guide"
            # else:
            #     continue  # Skip if it's not a "Getting Started Guide"

            # Extracting the model and other relevant fields
            model = response.css('div#mc-main-content h1::text').get(default='').strip()

            commercial_gym['model'] = model
            commercial_gym['product'] = product
            commercial_gym['type'] = type_doc
            commercial_gym['brand'] = "Precor"
            commercial_gym['source'] = "precor.com"
            commercial_gym['thumbs'] = response.urljoin(response.css('td.TableStyle-Lang_table-BodyE-Column1-Body1 img::attr(src)').get())
            commercial_gym['product_lang'] = product_lang
            commercial_gym['url'] = response.url

            yield commercial_gym
