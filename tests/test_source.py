"""本地来源契约检查，不包含尚未实现的采集逻辑。"""
import gzip
import http.client
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source.server import running_source

class SourceContract(unittest.TestCase):
    def request(self,url,payload=None,headers=None):
        parts=urlsplit(url);conn=http.client.HTTPConnection(parts.hostname,parts.port,timeout=10)
        body=json.dumps(payload).encode() if payload is not None else None
        conn.request('POST' if payload is not None else 'GET',parts.path+('?' + parts.query if parts.query else ''),body,headers or {})
        response=conn.getresponse();result=(response.status,dict(response.getheaders()),response.read());conn.close();return result
    def get(self,url,headers=None):return self.request(url,headers=headers)
    def post(self,url,payload):
        status,headers,body=self.request(url,payload)
        self.assertLess(status,300)
        return json.loads(body)
    def test_observable_source(self):
        with running_source() as (base,source):
            self.assertEqual(self.get(base+'/health')[0],200)
            self.post(base+'/__admin/advance',{'seconds':2})
            self.assertEqual(json.loads(self.get(base+'/health')[2])['time'],2)
            self.assertGreaterEqual(len(json.loads(self.get(base+'/__admin/log')[2])),3)

    def test_real_hover_and_frame(self):
        from playwright.sync_api import sync_playwright
        with running_source() as (base,s),sync_playwright() as p:
            b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page();page.goto(base)
            page.wait_for_selector('svg[data-revision="C01-2024"]')
            page.locator('circle').first.hover();page.wait_for_selector('#tip:visible');self.assertIn('零值',page.locator('#tip').inner_text())
            self.assertIn('万吨标准煤',page.frame_locator('#note').locator('main').inner_text())
            page.select_option('#year','2023');page.wait_for_selector('svg[data-revision="C01-2023"]');self.assertEqual(page.locator('circle').count(),2);b.close()

if __name__=='__main__':unittest.main()
