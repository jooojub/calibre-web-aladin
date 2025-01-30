# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2021 OzzieIsaacs
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

# Google Books api document: https://developers.google.com/books/docs/v1/using
from typing import Dict, List, Optional
from urllib.parse import quote
from datetime import datetime

import requests

from cps import logger
from cps.isoLanguages import get_lang3, get_language_name
from cps.services.Metadata import MetaRecord, MetaSourceInfo, Metadata

log = logger.create()


class Aladin(Metadata):
    __name__ = "Aladin"
    __id__ = "aladin"
    DESCRIPTION = "Aladin Books"
    META_URL = "https://www.aladin.co.kr/"
    BASE_URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx?"
    BASE_URL += "ttbkey=ttbsonginha22141002"
    BASE_URL += "&Cover=Big"
    BASE_URL += "&ItemIdType=ISBN13"
    BASE_URL += "&MaxResults=20&start=1&SearchTarget=Book&output=JS&Version=20131101"

    def search(
        self, query: str, generic_cover: str = "", locale: str = "en"
    ) -> Optional[List[MetaRecord]]:
        val = list()    
        if self.active:

            title_tokens = list(self.get_title_tokens(query, strip_joiners=False))
            if title_tokens:
                tokens = [quote(t.encode("utf-8")) for t in title_tokens]
                query = "+".join(tokens)
            try:
                results = requests.get(Aladin.BASE_URL + "&Query=" + query)
                results.raise_for_status()
            except Exception as e:
                log.warning(e)
                return None

            for result in results.json().get("item", []):
                val.append(
                    self._parse_search_result(
                        result=result, generic_cover=generic_cover, locale=locale
                    )
                )

        return val

    def _parse_search_result(
        self, result: Dict, generic_cover: str, locale: str
    ) -> MetaRecord:
        match = MetaRecord(
            id=result["itemId"],
            title=result["title"],
            authors=[result.get("author", "")],
            url=result["link"],
            source=MetaSourceInfo(
                id=self.__id__,
                description=Aladin.DESCRIPTION,
                link=Aladin.META_URL,
            ),
        )

        match.cover = self._parse_cover(result=result, generic_cover=generic_cover)
        match.description = result.get("description", "")
        match.languages = ["Korean"]
        match.publisher = result.get("publisher", "")
        try:
            datetime.strptime(result.get("pubDate", ""), "%Y-%m-%d")
            match.publishedDate = result.get("pubDate", "")
        except ValueError:
            match.publishedDate = ""

        match.series = self._parse_series(result=result)

        match.tags = self._parse_tags(result=result)
        match = self._parse_isbn(result=result, match=match)

        return match

    @staticmethod
    def _parse_isbn(result: Dict, match: MetaRecord) -> MetaRecord:
        match.identifiers["ISBN13"] = result.get("isbn13", [])
        match.identifiers["ISBN"] = result.get("isbn", [])
        return match

    @staticmethod
    def _parse_cover(result: Dict, generic_cover: str) -> str:
        if result["cover"]:
            cover_url = result["cover"]
            
            # strip curl in cover
            cover_url = cover_url.replace("&edge=curl", "")
            
            return cover_url.replace("http://", "https://")
        return generic_cover
    @staticmethod
    def _parse_series(result: Dict) -> str:
        if result.get("seriesInfo"):
            return result["seriesInfo"].get("seriesName", "")
        return ""

    @staticmethod
    def _parse_tags(result: Dict) -> str:
        if  result.get("categoryName"):
            tag = result.get("categoryName")
            return [tag.split(">")[-1]]
        return []