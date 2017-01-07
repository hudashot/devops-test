import datetime
import pytest
import responses

import beacon

SAMPLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><record xmlns="http://beacon.nist.gov/record/0.1/"><version>Version 1.0</version><frequency>60</frequency><timeStamp>1483739640</timeStamp><seedValue>5FA9E24BBA9462D363E7241912F3CF9C470E08481381C25D5B99A5890DD00A26FC1B884B3FADAD45459E3883AF25246B3A0FAE30554B0CAFDAC0B51424C3142D</seedValue><previousOutputValue>A6FB38E5A8B730DDE35448019F6E6D24D906C8BCE4C711A63F12089A721DC2B1B39224CA6DC0BB78519E1B21CD012BE5BE08FCCCB24C32C595CA40DEB2AD2753</previousOutputValue><signatureValue>D7BBD02B88C0DA63FB25B931C5BE2A01799E2301B802B21D19AD158B14F0FA4484082DCE775B2310C7874944A51C832DC670BD3B0A91B524D5FDFEE1BAFBE43574B457F6E4D52104B49B8C2CB6F4CA3BBB91DFE2DCA7B6E8CAE767B2452B1C34EC008506E5D87C9EB59356205DE572EAAC895D3B14327ADB7F5FFAFCA54B48336E99EB74C31102EB487D0A620001A29E0D14766B1B863494BB3218E93EDDC8441274D5AF45794805687B9609ED4C766E238217A171230F95B6262E3B4398DCC8584A8DBCDFC73A248BFCC5166F28E3959B6BCE07FDFE9337C6B062A04F5CACF04862F27CCE9945B7225837DC577EFA8D5AB151601ECB3576E4443E0E9EA55C1E</signatureValue><outputValue>3E3F13AB4786C101BEFE153B25F40490821B78B6AA77C5E76A2C912073A91866F2F7896E016907754E02161E4C2AA48B06766BFC48FFA568B1164D630D9818D5</outputValue><statusCode>0</statusCode></record>"""  # NOQA


class TestBeacon(object):

    @responses.activate
    def test_fetch_urls(self):
        count = 100
        for i in range(count):
            responses.add(responses.GET, "https://fake/{}".format(i),
                          body="response{}".format(i))
        urls = ["https://fake/{}".format(i) for i in range(count)]
        resp = list(beacon._fetch_urls(urls, timeout=1, concurrency=10))
        assert len(responses.calls) == count
        assert (sorted([r.text for r in resp]) ==
                sorted(["response{}".format(i) for i in range(count)]))

    def test_beacon_correct(self):
        b = beacon.Beacon(SAMPLE)
        assert b["version"] == "Version 1.0"
        assert b["outputValue"] == "3E3F13AB4786C101BEFE153B25F40490821B78B6AA77C5E76A2C912073A91866F2F7896E016907754E02161E4C2AA48B06766BFC48FFA568B1164D630D9818D5"  # NOQA

    def test_beacon_incorrect(self):
        with pytest.raises(RuntimeError):
            beacon.Beacon("This is not XML")

    @pytest.mark.parametrize("ts_from,ts_to,urls", [
        (1483746016, 1483746016,
         ["https://beacon.nist.gov/rest/record/1483746000"]),
        (1483746001, 1483746059,
         ["https://beacon.nist.gov/rest/record/1483746000"]),
        (1483746001, 1483746061,
         ["https://beacon.nist.gov/rest/record/1483746000",
          "https://beacon.nist.gov/rest/record/1483746060"]),
        (1483746000, 1483746119,
         ["https://beacon.nist.gov/rest/record/1483746000",
          "https://beacon.nist.gov/rest/record/1483746060"]),
        (1483746001, 1483746121,
         ["https://beacon.nist.gov/rest/record/1483746000",
          "https://beacon.nist.gov/rest/record/1483746060",
          "https://beacon.nist.gov/rest/record/1483746120"]),
    ])
    def test_generate_urls(self, ts_from, ts_to, urls):
        assert (list(beacon._generate_urls(
            datetime.datetime.fromtimestamp(ts_from),
            datetime.datetime.fromtimestamp(ts_to))) == urls)

    @pytest.mark.parametrize("dt", [
        datetime.datetime(2000, 1, 1, 1, 1, 17),
        datetime.datetime(2000, 1, 1, 1, 1, 17, 233),
        datetime.datetime(2000, 1, 1, 1, 1, 0, 233),
    ])
    def test_truncate_seconds(self, dt):
        assert (beacon._truncate_seconds(dt) ==
                datetime.datetime(2000, 1, 1, 1, 1))
