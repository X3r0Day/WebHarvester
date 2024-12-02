import requests
import os
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class AdvancedScraper:
    def __init__(self):
        self.request_count = 0
        self.visited_urls = set() # (Correct me if I'm wrong, making list for keeping check on visited can be so unefficient for more depths, right? If you can come up with something else, please create an issue!!)

    def extract_emails(self, html):
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return list(set(re.findall(email_pattern, html)))

    def extract_links(self, html, base_url):
        links = set()
        soup = BeautifulSoup(html, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            link = a_tag["href"]
            full_link = urljoin(base_url, link)
            if urlparse(full_link).scheme in ['http', 'https']:
                links.add(full_link)
        return list(links)

    def extract_by_selector(self, html, selector):
        soup = BeautifulSoup(html, "html.parser")
        return [element.get_text() for element in soup.select(selector)]

    def find_potential_xss_params(self, url):
        xss_params = []
        if "?" in url:
            params = url.split('?')[1].split('&')
            for param in params:
                param_name = param.split('=')[0]
                if param_name in ['q', 'search', 'test', 'id', 'page', 'query', 'user', 'action', 's', 'lang', 'p', 'item', 'blog', 'url', 'l', 'item', 'page_id', 'name', 'password', 'email', 'type', 'year', 'view', 'comment', 'showComment']:
                    xss_params.append(f"{url} ({param})")
        elif "=" in url:
            xss_params.append(f"{url} (single param)")
        return xss_params

    def crawl(self, url, depth, args):
        collected_data = []
        xss_urls = []

        if depth <= 0 or url in self.visited_urls:
            return collected_data, xss_urls

        print(f"Fetching URL: {url}")
        self.visited_urls.add(url)  # Say no to re-visit visited urls

        try:
            response = requests.get(url, timeout=10)  # Finally added timeout in case it stucks for infintely long
            self.request_count += 1
            html = response.text
            links = self.extract_links(html, url)

            if args.xss:
                xss_vulnerabilities = self.find_potential_xss_params(url)
                xss_urls.extend(xss_vulnerabilities)

            collected_data.append((url, html))
            for link in links:
                nested_data, nested_xss = self.crawl(link, depth - 1, args)
                collected_data.extend(nested_data)
                xss_urls.extend(nested_xss)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")

        return collected_data, xss_urls

def main():
    parser = argparse.ArgumentParser(description="Advanced Scraping Tool with Multiple Options")
    parser.add_argument("-u", "--url", help="Target URL to scrape", required=True)
    parser.add_argument("-e", "--emails", help="Scrape emails", action="store_true")
    parser.add_argument("-l", "--links", help="Scrape links", action="store_true")
    parser.add_argument("-s", "--selector", help="Scrape by CSS selector", default=None)
    parser.add_argument("-o", "--output", help="Save result in output file", default=None)
    parser.add_argument("-d", "--depth", help="Crawl depth for recursive scraping (default: 1)", type=int, default=1)
    parser.add_argument("--xss", help="Check for potential XSS vulnerabilities in links", action="store_true")
    parser.add_argument("--verbose", help="Enable verbose output", action="store_true")

    args = parser.parse_args()

    scraper = AdvancedScraper()
    collected_data, xss_urls = scraper.crawl(args.url, args.depth, args)

    results = {"emails": [], "links": [], "selector_data": [], "xss_vulnerabilities": []}

    for url, html in collected_data:
        if args.emails:
            results["emails"].extend(scraper.extract_emails(html))
        if args.links:
            results["links"].extend(scraper.extract_links(html, url))
        if args.selector:
            results["selector_data"].extend(scraper.extract_by_selector(html, args.selector))

    results["emails"] = list(set(results["emails"]))
    results["links"] = list(set(results["links"]))
    results["selector_data"] = list(set(results["selector_data"]))
    results["xss_vulnerabilities"] = list(set(xss_urls))

    if args.verbose:
        print(f"Total requests made: {scraper.request_count}")

    if args.output:
        with open(args.output, "w") as f:
            if args.emails:
                f.write("Emails:\n" + "\n".join(results["emails"]) + "\n")
            if args.links:
                f.write("Links:\n" + "\n".join(results["links"]) + "\n")
            if args.selector:
                f.write("Selector Data:\n" + "\n".join(results["selector_data"]) + "\n")
            if args.xss:
                f.write("Potential XSS Vulnerabilities:\n" + "\n".join(results["xss_vulnerabilities"]) + "\n")
    else:
        if args.emails:
            print("Emails:\n", "\n".join(results["emails"]))
        if args.links:
            print("Links:\n", "\n".join(results["links"]))
        if args.selector:
            print("Selector Data:\n", "\n".join(results["selector_data"]))
        if args.xss:
            print("Potential XSS Vulnerabilities:\n", "\n".join(results["xss_vulnerabilities"]))

    if args.verbose:
        print(f"Total requests made: {scraper.request_count}")

if __name__ == "__main__":
    main()
