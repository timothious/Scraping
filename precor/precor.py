import scrapy
from manual_scraper_ext.items import Manual

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
        # Extract the product path
        product = response.xpath('//html/@data-mc-toc-path').get(default='').strip()
        product_parts = product.split('|')
        if len(product_parts) > 1:
            product = product_parts[1].strip()

        # Extract the document types
        type_doc = response.css('div#mc-main-content h2::text').get(default='').strip()

        # Skip the item if the type is "AssaultBike Elite Product Documentation"
        if type_doc == "AssaultBike Elite Product Documentation":
            return

        # Extract the product language
        product_lang = response.css("html::attr(lang)").get().split("-")[0]

        # Extract the model name
        model = response.css('div#mc-main-content h1::text').get(default='').strip()

        if "and" in model:
            # Split the model on 'and'
            model_parts = model.split("and")

            # Extract the prefix from the first model part
            prefix = model_parts[0].strip().split(" ")[0]
            if 'Treadmill' in prefix:  # Check if the prefix is "Treadmill"
                prefix = "TRM"
                models = [f"{prefix} {part.strip().replace('Treadmill', '').strip()}" for part in model_parts]
            else:
                models = [part.strip() if part.strip().startswith(prefix) else prefix + " " + part.strip() for part in
                          model_parts]
        else:
            models = [model.strip()]  # Handle the case where there's no 'and'

        # Iterate over each PDF link in the table
        for item in response.css('table.TableStyle-Lang_table tr.TableStyle-Lang_table-Body-Body1'):
            file_url = item.css('td a::attr(href)').get()
            thumbnail = response.urljoin(
                response.css('td.TableStyle-Lang_table-BodyE-Column1-Body1 img::attr(src)').get())
            page_url = response.url

            for individual_model in models:
                manual = Manual()
                manual['file_urls'] = [file_url]
                manual['model'] = individual_model
                manual['product'] = product
                manual['type'] = type_doc
                manual['brand'] = "Precor"
                manual['source'] = "precor.com"
                manual['thumbs'] = thumbnail
                manual['product_lang'] = product_lang
                manual['url'] = page_url

                yield manual

