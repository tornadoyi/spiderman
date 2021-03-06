from __future__ import absolute_import

from collections import deque
from scrapy import signals
from scrapy.core.scheduler import Scheduler
from spiderman.core.managers import SpidermanManager
from spiderman.settings import ScrapySettingsAdapter



class SpidermanScheduler(Scheduler):
    def __init__(self, crawler):
        self._crawler = crawler
        self._pending_requests = deque()
        self._manager = SpidermanManager(ScrapySettingsAdapter(crawler.settings))

        # settings
        self._max_next_requests = crawler.settings.get('MAX_NEXT_REQUETS', 1)

    def __len__(self):
        return len(self._pending_requests)

    @property
    def crawler(self): return self._crawler

    @property
    def manager(self): return self._manager

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def has_pending_requests(self):
        return len(self) > 0

    def open(self, spider):
        # start manager
        self._manager.start(spider)

        # handle event
        spider.crawler.signals.connect(self.process_spider_error, signal=signals.spider_error)
        spider.crawler.signals.connect(self.process_item_scraped, signal=signals.item_scraped)
        spider.crawler.signals.connect(self.process_item_dropped, signal=signals.item_dropped)


    def close(self, reason):
        self._manager.stop(reason)

    def enqueue_request(self, request):
        self._manager.add_requests([request])

    def next_request(self):
        requests = self._manager.get_requests(self._max_next_requests)
        if len(requests) > 0:
            self._pending_requests.extend(requests)
        return self._pending_requests.popleft() if self._pending_requests else None


    def process_download_exception(self, request, exception, spider):
        return self._manager.process_download_exception(request, exception, spider)


    def process_spider_exception(self, response, exception, spider):
        return self._manager.process_spider_exception(response, exception, spider)


    def process_spider_error(self, failure, response, spider):
        return self._manager.process_spider_error(failure, response, spider)


    def process_item_scraped(self, item, response, spider):
        return self._manager.process_item_scraped(item, response, spider)

    def process_item_dropped(self, item, spider, exception):
        return self._manager.process_item_dropped(item, spider, exception)